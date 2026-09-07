# Quyết định triển khai: RUN chủ động gọi model, thay vì chờ ChatGPT tiếp tục

Ngày: **07/09/2026**. Repository: `E:\DEV\Codex-web`. Baseline đọc: `main` / `58dfd3093d7a05f6999fe93e15c94050aa51d204`, working tree có concurrent WIP.

Trong lúc nghiên cứu, một tác nhân đồng thời đã commit HEAD thành `d02c6e2ef1506a25819dd65ec7811c4ac7c01edc`. Đã so hai commit: bridge/candidate/workflow/orchestration-control/controller-continuity/server/runtime-background/patching được dùng trong quyết định này không đổi. Hash của bridge, workflow và patching cũng khớp trước/sau. Đây không phải commit do task nghiên cứu thực hiện.

Đây là kết luận thiết kế và đề xuất triển khai theo yêu cầu phân tích sâu của người dùng. Nó bổ sung, không sửa lại lịch sử của [báo cáo khả thi](260907_DURABLE_CONTINUATION_FEASIBILITY_ASSESSMENT.md). Không phải code đã triển khai, authority đã được cấp, hay pilot đã chạy.

## 1. Quyết định duy nhất được khuyến nghị

**Xây một vòng thực thi có giới hạn bên trong Coding Tools MCP, gắn với RUN hiện hữu; dùng Codex App Server bridge hiện có làm bộ suy luận không có quyền gây tác dụng phụ.** ChatWeb xác định hợp đồng và giữ final acceptance; MCP tự vận hành phần đọc bằng chứng → đề xuất sửa → áp dụng có kiểm soát → kiểm tra → sửa tiếp trong hợp đồng đã giao.

Tên triển khai đề xuất: `run_continuation`, không phải một Goal Engine hoặc Durable Agent platform mới.

Quyết định này loại ordinary ChatGPT turn khỏi đường bắt buộc để từng bước sửa lỗi tiến lên. Không cần chờ một API có thể đánh thức chính conversation ChatGPT đang mở. Không cần thay product bằng upstream Rust, Temporal, Work Cloud hoặc Workspace Agent đã publish.

**Mục tiêu v1:** người dùng giao một yêu cầu kỹ thuật có phạm vi và phép kiểm chứng rõ, cho phép chạy nền, rồi đóng browser; máy vẫn chạy chu trình sửa/kiểm tra đến `ACCEPTING` hoặc một lý do dừng thật. Khi quay lại, người dùng/controller review một kết quả có bằng chứng thay vì liên tục gõ “tiếp tục”.

**Không hứa v1:** model ChatGPT Web ban đầu tự sống lại; tự xác nhận outcome nghiệp vụ; mọi OS process sống qua restart/reboot; tự publish/deploy; tự mở rộng phạm vi hoặc chi phí vô hạn.

Đây là GO cho một implementation hẹp, không còn là kết luận “hãy đi tìm host rồi tính tiếp”. Host suy luận được chọn là **Codex App Server đã có trong dự án**. Khả năng đăng nhập/model trên cài đặt thật là preflight vận hành cần kiểm tra lúc canary, không phải lý do để tiếp tục để ngỏ lựa chọn kiến trúc.

## 2. Lập luận kỹ thuật: vấn đề là vòng phụ thuộc, không chỉ là persistence

Workflow hiện tại có vòng:

```text
ChatGPT ra quyết định → MCP thực hiện → kết quả → ChatGPT ra quyết định tiếp
```

Khi bước tiếp theo cần suy luận và ChatGPT không còn turn, vòng bị đứt. Thêm checkpoint/Wake chỉ giữ được câu hỏi “còn phải làm gì”; chúng không tạo bên có khả năng trả lời câu hỏi đó.

Điều kiện tiến triển sau mất chat là:

```text
công việc còn hợp lệ
AND có executor/driver đang sống hoặc có thể được khởi động hợp lệ
AND có bên gọi được model cho quyết định mới
AND còn quyền, ngân sách và thông tin cần thiết
```

Persistence giải quyết khả năng phục hồi trạng thái. Một consumer có quyền gọi model mới giải quyết khả năng tiếp tục tiến triển. Đây là hai tính chất khác nhau.

Không thể đồng thời yêu cầu cả ba điều sau khi chưa có host callback:

1. chỉ chính ordinary ChatGPT Web model được phép suy luận;
2. ChatGPT không còn thực thi turn;
3. những quyết định chưa biết trước vẫn tự được đưa ra.

Thiết kế được chọn thay điều kiện 1 ở **phần thi hành được giao**: Codex lane suy luận từ hợp đồng và bằng chứng, còn ChatWeb giữ quyết định phạm vi và nghiệm thu. Đây là thay đổi trách nhiệm được nêu công khai, không phải âm thầm impersonate ChatGPT.

Official App Server có thread persistence/resume, turn start, output schema và observation events. Bridge local đã gọi các primitives này. Vì vậy phía MCP có đường chủ động yêu cầu inference mà không cần ChatGPT Web callback. [OpenAI App Server](https://learn.chatgpt.com/docs/app-server).

## 3. Ý tưởng tạo khác biệt: tách quyết định khỏi tác dụng phụ

### 3.1. RUN là nơi điều khiển; model là thành phần có thể thay phiên

```text
ChatWeb / người dùng
    │ chốt contract + quyền thi hành có hạn
    ▼
RUN + continuation cursor trong canonical ledger
    │
    ├─ MCP thu thập bằng chứng đã được phép
    ├─ Codex đề xuất next action có cấu trúc
    ├─ MCP kiểm tra scope / generation / preimage / budget
    ├─ MCP áp dụng patch hoặc chạy phép kiểm chứng đã duyệt
    └─ MCP ghi receipt và chọn bước kế tiếp
                │
                ├─ lỗi kỹ thuật trong scope → REPLAN có bằng chứng → vòng tiếp
                ├─ thiếu quyền/ý nghĩa/budget → pause có lý do
                └─ proof đủ → ACCEPTING → ChatWeb/người dùng nghiệm thu
```

Vòng suy luận và vòng tạo tác dụng phụ nằm dưới một execution owner của RUN. Không có hai agent độc lập cùng viết checkout.

### 3.2. Model không giữ quyền; model chỉ đề xuất

Đầu ra model có một discriminated union nhỏ, không phải ngôn ngữ workflow tổng quát:

| Action đề xuất | Driver thực hiện |
|---|---|
| `READ` | Đọc file/range hoặc tìm kiếm bounded trong read allowlist, trả evidence có hash |
| `PATCH` | Exact replacements/new files trong write allowlist; kiểm tra preimage và candidate schema |
| `READY` | Yêu cầu kết thúc thi hành; driver tự kiểm lại đủ proof/coverage, không tin tự khai |
| `BLOCKED` | Ghi lý do có cấu trúc và pause; không tự xin thêm quyền |

Phép kiểm chứng do driver chọn từ danh sách đã được duyệt trong hợp đồng, không nhận arbitrary shell do model tự tạo. Sau mỗi patch, chạy tập checks liên quan; chỉ rerun check bị invalidated hoặc check cần cho trạng thái candidate mới. Không chạy cả suite sau mọi lần đọc.

Cho phép `READ` làm vòng sửa thích nghi với bằng chứng mới mà không bắt ChatWeb dự đoán trước mọi nhánh. Nhưng model không có shell/MCP/browser/network tools, không được gọi `accept`, không sửa file trực tiếp, không delegate thêm. Mọi action đều qua broker deterministic của MCP.

### 3.3. Suy luận có thể bị bỏ; tác dụng phụ không được lặp mù

Đây là lợi thế lớn của topology trên:

- Nếu model process chết trước khi output được chấp nhận, có thể bỏ output chưa xác minh và suy luận lại từ checkpoint.
- Nếu response đến muộn từ generation cũ, bỏ nó trước khi áp dụng.
- Nếu chạy lại inference tạo một đề xuất khác, chỉ một đề xuất khớp action sequence/current evidence được commit. Không cố tái hiện token hoặc private reasoning của model cũ.
- Nếu tác dụng phụ đã xảy ra mà receipt chưa ghi xong, phải reconcile effect; không gọi lại model rồi áp dụng lại như chưa từng chạy.

Không hứa model inference deterministic hoặc provider billing exactly-once. Chỉ coi inference là hoạt động không có quyền sửa workspace; correctness nằm ở receipt/journal của driver.

Mẫu phân biệt event history với hoạt động bên ngoài có tiền lệ trong durable workflow systems. Ở đây chỉ áp dụng nguyên lý, **không cài Temporal hoặc xây lại framework tương tự**. [Temporal replay model](https://docs.temporal.io/workflow-execution).

### 3.4. Độ bền ngữ nghĩa quan trọng hơn giữ cùng PID/thread

Context bắt buộc khi resume là contract, constraint, evidence IDs, current source hashes, pending criterion/action và các tác dụng đã được ghi nhận. Codex thread history chỉ là cache hỗ trợ suy luận, không phải canonical authority.

Thread còn hợp lệ thì resume để tiết kiệm context. Thread không đọc được/không xác minh được thì không nhận một thread khác theo “gần nhất”; ghi typed failure, giải quyết request đang bất định, rồi mới tạo một thread mới từ capsule khi hợp đồng cho phép. Context của iteration mới phải nói rõ file/evidence nào đã thay đổi; không coi cache cũ là current truth.

Vì vậy có thể tiếp tục cùng **công việc** dù không tiếp tục cùng **process**. Đây là bảo đảm có thể thiết kế và kiểm thử, khác lời hứa giữ mọi process sống qua restart.

## 4. Vì sao chọn đúng phương án này cho repository hiện tại?

Tên module Python trong bảng thuộc `resources/coding-tools-mcp/coding_tools_mcp/`.

| Bằng chứng hiện có | Hệ quả thiết kế |
|---|---|
| `codex_bridge.py:587`, `:671`, `:977`: persistent lane, resume và `turn/start` | Có đường gọi inference chủ động; không cần thêm provider tích hợp mới |
| `codex_bridge.py:54`, `:969`, `:985`: profiles, read-only/no-network, per-turn schema | Giữ sandbox; thêm profile no-tools dành riêng cho decision candidate, không biến deep-code hiện có thành unrestricted agent |
| `agent_candidate.py:519`, `:664`: validate candidate, exact paths, model output trước patch | Reuse conversion/validation thay vì cho model ghi trực tiếp |
| `workflow_tools.py:1285`, `:1335`: candidate một lượt, thất bại trả về controller | Đây là đường đứt cần nối: feed failure/evidence vào bounded continuation, không chỉ thêm storage |
| `workflow_tools.py:788`: `retry_mode=manual_replan_only` | Automatic repair trong scope là **policy change có chủ đích**, không phải bật option đã an toàn sẵn |
| `workflow_tools.py:1570`: proof xong vào `ACCEPTING` | Giữ final acceptance barrier, không sửa `ACCEPTING` thành hoàn tất tự động |
| `orchestration_control.py:35`, `:750`: state machine và new WAVE sau REPLAN | Giữ RUN; retry kỹ thuật có WAVE mới khi semantics hiện tại yêu cầu, không tạo TaskAttempt song song |
| `server.py:1258`: controller checks dựa trên request identity | Cần authority path riêng cho delegated driver; không lấy request context cũ làm bằng chứng một ChatWeb client vẫn online |
| `runtime_background.py:26`: result/execution thuộc MCP process | Dùng cơ chế worker hiện có cho browser-loss v1; cursor/result cần persist, không chỉ giữ `Event` trong memory |
| `file_tools.py:629`, `patching.py:94`: exact hashes, atomic per-file rename và rollback trong process | Có nền apply an toàn nhưng chưa phải transaction atomically gắn với SQLite hay recovery qua hard crash |

Mode hiện tại `bounded_candidate` chỉ cho Mini/Luna; route `sol_xhigh` thuộc `deep_single_lane` (`workflow_tools.py:705`). Candidate-only là topology, không đồng nghĩa bắt buộc dùng tên mode `bounded_candidate`. Thiết kế v1 dùng **explicit `sol_xhigh` / `deep_single_lane` với no-tools candidate profile**; không thay global `execution_route=auto`, không làm model cascade, không tự bật Max/Ultra.

Model thực tế/effort phải được bridge xác nhận khi chạy. Dùng route đã chỉ định là quyết định kỹ thuật cho workstream này, không phải claim rằng provider canary đã thành công hoặc chi phí hiện được đo.

Hai gap chính xác của bridge phải đóng, không thể giải chỉ bằng truyền `lifetime=persistent`:

1. `deep_code` hiện bật shell; feature flags/instructions hiện hữu chưa chứng minh mọi built-in tool đều bị tắt. `CODING_TOOLS_MCP_CODEX_ARGV` còn có thể thay default launch args. Profile mới phải giữ exact validated launch/config, fail closed với custom-argv không được chứng nhận, không inherit MCP/apps/plugins, giữ sandbox read-only/no-network và kiểm tra negative tool behavior. Không ghi “no-tools đã có” chỉ vì prompt yêu cầu như vậy.
2. `resume_persistent_thread` hiện `thread/read(includeTurns=False)` rồi resume và launch turn mới. Khi old dispatch chưa có terminal receipt, cần read/observe/reconcile riêng trước đó. Nếu installed protocol không phân loại được old turn, pause unknown; không suy từ thread tồn tại rằng được phép dispatch tiếp.

`_MAX_DEADLINE_MS=30000` là clamp hiện tại cho bounded observe/decision deadline; `deadline_ms=0` không phải hard deadline. Driver không nên tăng mọi profile lên thời gian dài: dùng dispatch/observe bất đồng bộ có cancel riêng và ngân sách tổng RUN, chỉ thêm giới hạn thích hợp cho profile mới sau focused proof.

## 5. Hợp đồng thi hành: quyền phải tồn tại độc lập với socket chat

### 5.1. Nội dung được cấp một lần

Public entry đề xuất vẫn là `agent_workflow`; thêm object `continuation` explicit, mặc định không bật. Object là yêu cầu cấp quyền, không phải authority do client tự khai.

Runtime sau khi kiểm tra user intent và authenticated controller mới tạo một grant immutable gắn với RUN:

```text
problem_id + problem_revision + contract_hash
run_id + workspace_id + allowed source boundary
issuer/controller identity + issuance receipt
read_paths + write_paths + protected_paths
approved_checks (argv/cwd/environment policy/check-definition hashes)
fixed route/profile + maximum duration/calls/repair attempts
allowed recovery: same-scope technical repair only
acceptance_mode: controller_required
restart policy: recover only after official runtime admission
activation epoch + admission receipt + runtime behavior identity
```

Một chuỗi objective hoặc lời “hãy làm đến cùng” không tự cấp quyền sửa mọi file/chạy mọi lệnh. Hợp đồng giới hạn cụ thể mới quyết định driver được tiếp tục đến đâu.

V1 chỉ nhận bugfix/feature kỹ thuật với phạm vi rõ và oracle đủ mạnh; không nhận schema migration, credentials/IAM, financial semantics, production systems, publish/deploy hay self-modifying continuation/runtime control code. Những loại này vẫn cần controller trực tiếp.

### 5.2. Không giả ChatWeb online; không tạo writer thứ hai

Có hai thời hạn khác nhau:

- Session/controller attachment là quyền của endpoint tương tác hiện tại.
- Execution grant là quyền thi hành một packet đã được phê duyệt trong một khoảng có hạn.

ChatWeb rời đi không làm packet đã cấp quyền biến mất. Nhưng runtime không được tự renew một “ChatWeb online lease” bằng identity sao chép để hợp thức hóa mình.

Thiết kế cần một **delegated execution context có provenance riêng**. Broker kiểm tra grant, exact RUN, validity/revocation, runtime generation và existing write fence. MCP vẫn là sole writer; model lane không nhận grant hoặc write fence. `_require_hub_controller` tiếp tục bảo vệ accept/reject/contract change; không nới toàn bộ hàm này để background path chạy được.

Đặc biệt `identity is None` hiện có đường trả `None` trong `_require_hub_controller`. Driver mới phải thiếu grant là DENY, không được coi thiếu identity là local trusted bypass.

### 5.3. Takeover và cancel là giao thức, không phải heartbeat heuristic

Read-only status từ ChatWeb mới không cướp quyền driver. Khi người dùng muốn can thiệp có mutation/đổi contract:

1. revoke execution grant bằng atomic update trong ledger;
2. fence generation cũ, ngừng nhận action mới;
3. chờ action đang apply/check đến safe point hoặc quiesce qua đúng owner;
4. ghi trạng thái thực của effect đang dở;
5. mới chuyển quyền tương tác/ghi theo existing lease path.

Revoke không quay ngược effect đã commit. Không hứa cancel tức thì khi đang ở critical section. Controller acceptance vẫn phải kiểm tra exact receipt của candidate mới nhất.

Thay đổi contract/route/scope cần cấp lại grant; model không thể đưa lý do văn bản để tự thay chúng. Ordinary endpoint lease hết hạn không tự chuyển hoặc mở lại assignment của execution grant.

## 6. Persistence tối thiểu, không thêm một thế giới Task song song

Giữ Problem Revision/RUN/WAVE/Job/Proof làm identity chính. Thêm đúng một projection typed cho continuation của RUN trong **cùng canonical ledger**, không DB mới:

```text
run_continuations
  run_id (unique/FK)
  policy_json + policy_sha256 + issuing_receipt
  enabled + pause_reason + revoked_at
  driver_generation + claimed_runtime_instance
  next_action_seq + consumed_event_seq
  pending_action_id + pending_job_id
  lane_id + thread_id + last_turn_id
  remaining budgets / reserved inference calls
```

Đây là cursor/authorization của một execution packet, không thêm Goal state machine. Goal status lấy PRL; execution state lấy EOCL; Job state lấy managed job receipts. `pause_reason` chỉ nói driver chưa được dispatch tiếp.

Các bước/effect records dùng existing `events`, `idempotency_records`, `agent_lanes`, `managed_process_jobs`, `checkpoints`. Nếu payload vượt giới hạn, dùng artifact content-addressed trong `.coding-tools` kèm policy redaction; không đưa transcript hay credentials vào evidence. Context và log cần thiết cho proof có retention riêng, không serialize Python thread/Popen handle.

`coordination_messages` có thể phát thông báo thay đổi cho UI/ChatWeb, nhưng **không dùng generic ACK làm authoritative wake consume hoặc effect commit**. Wake lúc này là delivery optimization: nguồn thật để startup driver là RUN cursor và event sequence, không phụ thuộc một message đã được nhận đúng một lần.

Chỉ scan continuation được cấp quyền và chưa terminal, không scan mọi `runs.status=active`. Những stale RUN/P5 anchors/awaiting-acceptance từ lịch sử không tự trở thành workload.

## 7. Vòng thực thi chính xác

```text
read RUN + continuation row + relevant receipts
validate grant / admission / runtime generation / expected source
if acceptance barrier or paused/revoked/budget exhausted: stop dispatch
if pending Job: observe same Job; do not start replacement
if pending effect: reconcile before any new model request
if approved deterministic step is known: execute it without asking model
else:
    reserve bounded inference request + sequence in ledger
    ask bridge-owned Codex thread for one structured action
    observe terminal result; validate output and evidence bindings
    persist accepted decision under current sequence/generation
if PATCH:
    journal pre/post images -> apply through MCP -> record effect receipt
    run approved relevant checks
if technical failure within contract:
    record typed failure + changed evidence
    existing REPLAN/new-WAVE path -> next decision
if all current proof obligations satisfied:
    mark_accepting -> persist operator-visible report -> stop driver
```

Không gọi đệ quy `agent_workflow` dưới một request context giả. Tách một execution step từ đường đang có để interactive path và driver cùng dùng; chỉ đổi điều phối vòng đời, không copy/paste cả workflow/mutation/validation implementation.

### Budget và điều kiện dừng v1

Giá trị khởi đầu đề xuất, là policy thiết kế chứ không phải budget người dùng đã cấp: một RUN/driver và một model request đang chờ; tối đa 12 decision turns, 3 patch attempts, 15 phút. Request thực phải được operator cấp trong giới hạn đó hoặc cấu hình đã được duyệt. Không tự tăng khi sắp hết.

- Cùng normalized failure + cùng relevant source/evidence + không có hành động khác: dừng vì no-progress, không gọi model thêm chỉ để lặp lời giải.
- Có patch mới/evidence mới vẫn bị giới hạn bởi attempt/call/time budget, không bắt buộc số failed tests giảm đơn điệu.
- Chờ Job dùng observation event/cursor và bounded timeout, không gọi model để hỏi “test xong chưa”.
- Reserve lượt gọi trước dispatch. Usage chưa rõ không bằng zero; cancel provider là best effort, không hứa hard billing cap theo đồng tiền nếu provider chưa cung cấp primitive đó.
- Capacity/authentication/schema error không kích hoạt model cascade. Ghi typed pause/retry policy có hạn, không retry không đổi.

## 8. Crash/replay: nơi cần đầu tư kỹ thuật thật sự

### 8.1. Phân biệt action identity với request transport ID

Mỗi action có identity ổn định gắn `run_id`, grant revision, action sequence và normalized request/evidence hash. `driver_generation` là freshness guard của consumer, không dùng để tự biến cùng pending action thành một tác dụng mới sau restart.

Database transaction ghi intent trước effect; completion receipt phải khớp pending action và current generation. Nhưng SQLite không commit nguyên tử cùng filesystem/process launch. Cần xử lý khoảng mù giữa hai hệ thống, không che bằng một UUID.

| Điểm lỗi | Cách xử lý đã chốt |
|---|---|
| Chưa gửi model | Dùng cùng reserved request hoặc hủy reserve có receipt; không giả đã tiêu thụ |
| Đã gửi model nhưng mất phản hồi | Read/observe đúng thread/turn nếu xác minh được; không blind `turn/start` trên một turn đang chạy |
| Model output đến muộn sau revoke/takeover | Bỏ proposal bằng generation/sequence guard; model không có tool nên chưa sửa workspace |
| Model output đã persist nhưng apply chưa chạy | Validate lại expected source/fence rồi xử lý chính pending action |
| Patch applied, SQLite receipt chưa có | So pre/post manifest; nếu toàn bộ postimage khớp, ghi receipt `effect_reobserved`, không apply lần hai và không tuyên bố test PASS |
| File set đang ở trạng thái mixed/mất path sau hard crash | Pause `PATCH_RECOVERY_REQUIRED`; giữ backups/manifest; không auto rollback lên concurrent edits |
| Job đã chạy nhưng dispatch receipt chưa đầy đủ | Resolve durable admission và exact process identity; unknown thì không tự chạy lại |
| Job hoàn tất trong lúc browser đóng | Ghi terminal receipt/output đủ dùng; driver tiếp tục, không cần event gửi vào browser |
| MCP restart | Worker cũ có thể chết; runtime mới chỉ claim cursor sau supported admission và unknown-effect reconciliation |
| Full-clean cần connector/activation gate | Giữ pause đúng gate; không fake rediscovery/ACK để giữ lời hứa tự động |
| Máy reboot | Không giữ cùng OS process; tiếp tục work từ receipts hoặc yêu cầu xử lý unknown effect |

`AtomicPatchCommitter` hiện dùng per-file rename + rollback trong exception handler. Hard process crash có thể không chạy handler; vì vậy journal của continuation phải lưu pre/post hashes và **backup/temp mapping trước rename** cho các apply do driver thực hiện. Không gọi “atomic all-files + ledger” khi nền tảng không cung cấp transaction đó.

V1 cố ý fail closed với mixed file set thay vì xây một distributed transaction/auto-repair engine. Browser-loss thông thường vẫn tự tiến; hard-crash giữa commit là trạng thái cần phục hồi có bằng chứng. Muốn nâng bảo đảm sau này phải có named use case và real-process proof, không đổi tên trạng thái cho đẹp.

## 9. Phạm vi restart và process owner

Driver ở **Coding MCP hiện có**; Recovery Host chỉ quản lý lifecycle/admission như hiện tại. Không chuyển model loop, SQLite writer hoặc test executor vào Recovery Host. Không tạo service/scheduled task mới, không tắt Windows kill-on-close.

Code lifecycle hiện phân biệt đóng UI và dừng dịch vụ: `electron/main.js:765` dùng `keepRunningOnClose`; nhánh còn lại có thể yêu cầu stop runtime. Chế độ “chạy nền đến review” phải làm rõ đóng view/detach khác nút dừng dịch vụ, dùng existing keep-service path với lựa chọn người dùng minh bạch. Không tự đổi global setting trong một request nghiên cứu, và user chủ động stop service/cancel thì phải dừng.

V1 thiết kế rõ hai mức:

- **Browser-independent execution:** Closing browser/ordinary turn không cancel grant; MCP/bridge còn sống thì vòng tiếp tục đến proof-ready hoặc explicit stop.
- **Restart-resumable work:** Sau restart hợp lệ, đọc cursor/receipts và xử lý đúng uncertainty; không bảo đảm mọi Job sống sót, không tự vượt activation/connector gate.

Controlled refresh khi driver active phải quiesce/ghi checkpoint hoặc refuse bằng lifecycle guard hiện có. Self-update runtime trong chính grant bị cấm ở v1. Source changes do patch của driver cập nhật expected source receipt; drift từ actor khác hoặc runtime-behavior change không được coi là own progress.

Existing lane/bridge primitives không tự chứng minh Recovery Host admission hay full controller authority. Driver phải validate tại entry và trước effect; không suy rằng gọi được `_coordination_lane` hoặc `thread/resume` nghĩa là có quyền. Full-clean chỉ được dispatch tiếp sau exact supported `READY`/admission receipt; các state `STARTING`, `VERIFYING`, `READY_COMMITTED`, `FAILED` không đủ. Khi một epoch mới được hợp thức hóa, record adoption receipt nối predecessor → new runtime, tăng driver generation và giữ nguyên scope/budget/expiry; không replay receipt epoch cũ làm current authority.

## 10. Những lựa chọn bị loại và lý do

| Phương án | Quyết định |
|---|---|
| Prompt “không được dừng”, context dài hơn | Loại: không tạo inference consumer khi host không còn turn |
| Chỉ thêm AgentTask/Wake/upstream schema | Loại làm giải pháp chính: giữ được work nhưng không đóng vòng suy luận |
| UI follow-up bridge | Không làm correctness/liveness dependency: mất UI thì mất consumer; chỉ dùng notification/reattach sau này |
| Workspace Agents/Work Cloud | Không chọn cho v1: thêm account/published-agent/host integration dependency trong khi bridge local đã có |
| Codex worker ghi trực tiếp primary checkout | Loại: làm hai authority và mất effect broker/fencing của MCP |
| Native goal mode chạy tùy ý với nhiều tools | Không chọn v1: có thể tạo loop nhưng khó ràng buộc từng effect/proof với ledger hiện tại; native goal không thay RUN acceptance |
| Chuyển sang isolated worktree workflow toàn phần | Chưa chọn: thêm baseline-import/diff-integration lifecycle không cần để giải bounded primary-checkout packet; concurrent protected scope phải deny |
| Tắt kill-on-close hoặc adopt PID | Loại: đánh đổi safety boundary để che restart limitation |
| General scheduler, nhiều agent, routing mới | Loại: use case đầu là một RUN, một model lane, một writer; không cần framework |

## 11. Gói triển khai và tiêu chí nghiệm thu

Không yêu cầu thêm natural cohort trước khi viết unit/contract implementation cho dependency gap đã xác định. Natural pilot dùng để kiểm chứng UX/effectiveness sau khi safety gates đủ, không thay phân tích kiến trúc.

### Gói 1 — Hợp đồng quyền và cursor bền vững

- Module mới đề xuất `coding_tools_mcp/run_continuation.py`: typed policy/cursor/store mixin trong same ledger; không đổ thêm subsystem lớn vào `orchestration_ledger.py`.
- `tool_schema.py`: explicit `continuation` trên `agent_workflow`; trạng thái/pause/revoke nằm trên `task_control` hiện có. Tám public tools không đổi; schema/contract hash vẫn phải version/activation đúng.
- `workflow_tools.py`, targeted authority hook: grant issuance và delegated execution path, giữ accept/reject authority riêng.
- Tests mới đề xuất `test_run_continuation.py`: issuance, replay conflict, no identity/no grant deny, expiry, revocation, lease takeover race, fixed route, scope/check hash constraints.

**Gate:** driver thiếu grant hoặc stale generation không thể apply/run-check; copy object `hub_client` không biến worker thành active ChatWeb controller; không thêm auto-route authority.

### Gói 2 — Vòng sửa tự động một RUN

- `codex_bridge.py`: profile no-tools cho explicit Sol decision lane; persistent handle, observe không giữ HTTP call; per-decision timeout và whole-RUN budget tách riêng. Không nâng default deadline của các review/candidate profiles khác.
- `tool_contract.py`: map profile/route và expose đúng lifecycle/deadline semantics, không ghi đè các route mặc định hiện có. Kiểm tra custom argv và effective capability boundary, không chỉ test prompt text.
- `agent_candidate.py`: reuse exact candidate validation; schema READ/PATCH/READY/BLOCKED strict, bounded outputs.
- `workflow_tools.py`: tách single attempt step, deterministic proof và typed same-scope REPLAN; driver gọi nội bộ dưới delegated context.
- `runtime_background.py`: task chạy trong runtime chứ không bị kết thúc bởi tool-response disconnect; persist cursor và material outputs/receipts.

**Gate:** scripted model fixture trả patch sai → check fail → patch đúng → check pass; driver tự tới `ACCEPTING` mà không có thêm controller request. Scope expansion, sửa oracle, READY giả hoặc model output malformed đều không qua.

### Gói 3 — Effect journal và phục hồi

- `file_tools.py` / `patching.py`: continuation-specific manifest hooks trước/giữa/sau apply; không giảm baseline checks/rollback của interactive path.
- Existing job admission/observation và `idempotency_records`: action binding, retained result/output reference, unknown-dispatch classification.
- Runtime startup: claim một continuation eligible bằng CAS, reobserve receipts, không revive terminal RUN hoặc stale background Python worker.

**Gate:** fault injection tại từng ranh giới ở mục 8, hai driver cùng claim, stale model output sau cancel, browser disconnect và runtime restart fixture. Không duplicate admitted effect; mixed filesystem state phải pause; không dùng PID presence làm ownership proof.

### Gói 4 — UX và một canary đúng mục tiêu

- UI hiện có hiển thị Running / waiting check / paused reason / awaiting acceptance từ canonical projection; pause/revoke có receipt.
- Controlled activation và real provider canary chỉ thực hiện khi task triển khai có authority tương ứng. Test đóng browser phải giữ executor/máy hoạt động; restart/reboot là ca riêng.
- Một natural bugfix đủ hẹp: đo số user reprompt, số semantic calls, repair cycles, time-to-proof-ready, acceptance/outcome riêng và observed usage.

**Gate phát hành tính năng:** không có prompt “tiếp tục” giữa các repair cycles; user cancellation/takeover luôn có hiệu lực tại safe point; fixed scope và no duplicate effect; proof/currentness/acceptance truth giữ nguyên. Không claim phần trăm nhanh hơn hoặc rẻ hơn trước số liệu.

## 12. Nghiệm thu đến đâu thì đúng lời hứa?

`ACCEPTING` là **hoàn tất thi hành để review**, chưa phải Problem resolved. Đây là stop point v1 được chọn, không lén coi Goal đã xong.

Phần “không cần nhắc tiếp tục” được giải trong vòng engineering: phân tích lỗi, sửa, kiểm tra, sửa tiếp. Một lần nghiệm thu cuối hoặc quyết định ngoài scope là can thiệp có ý nghĩa, không phải người dùng làm scheduler.

Nếu sau này yêu cầu “không ai nghiệm thu mà full Problem vẫn tự confirmed”, phải có một authority/outcome policy riêng được người dùng chấp thuận. Không mở nó trong v1 và không gọi test PASS là independent business outcome. Cũng không bỏ manual acceptance chỉ vì nó làm số autonomy đẹp hơn.

## 13. Kết luận triển khai

**Nên triển khai `run_continuation` theo bốn gói trên, chọn existing Codex bridge làm inference consumer ngay từ đầu. Không port full Durable Agent runtime; không chờ ordinary ChatGPT auto-resume; không đặt correctness vào UI wake.**

Phần đổi mới là đảo quan hệ: từ *model turn sở hữu workflow* thành *RUN có hợp đồng sở hữu vòng gọi model và effects*. Model context là cache, source/proof/effect receipts là truth. Nhờ model không có quyền tạo tác dụng phụ, runtime có thể bỏ/replay inference khi cần mà không tự nhân đôi công việc.

Cần sửa thật ba boundary: quyền thi hành sau khi endpoint rời đi, automatic technical REPLAN có giới hạn và journal/cursor qua process failure. Đây không phải một switch đang tắt; cũng không cần một platform mới.

### Trạng thái bằng chứng của tài liệu

- Đã đối chiếu current source ở các điểm bridge, candidate, workflow, authority, background và patching; dùng read-only scoped workers cho hai câu hỏi độc lập. Controller tự quyết định kiến trúc, không xem worker agreement là approval.
- Đã kiểm tra CLI cục bộ `codex app-server --help` và official App Server lifecycle contract; không khởi động provider, không gọi inference, không đọc credentials.
- Không rerun 12 tests từ lượt khả thi chỉ để tăng số proof. Chúng vẫn chỉ là historical focused receipts cho behaviors cũ, không phải tests của driver mới.
- Không sửa source, runtime evidence hoặc policy đang vận hành. Không migration, activation, service restart, Git delivery hoặc publish/deploy. Tài liệu này là authority proposal để triển khai, chưa phải authority granted.
- Baseline còn dirty/concurrent; implementation phải pin lại đúng source packet. Không nhận WIP của task khác là kết quả của nghiên cứu này.
- Hai packet chỉ đọc hoàn tất: bridge/candidate gaps và Recovery Host/process lifetime; không giao worker quyết định authority hay triển khai source. File mới được kiểm tra whitespace/conflict markers, cân bằng code fences, liên kết local và scoped sensitive-content guard; đều không có findings. Không diễn giải document QA thành proof của driver chưa viết.
- Source discriminator postflight: `workflow_tools.py` SHA-256 `0ff45661db8196070769094f993f8d5b096c8d5a6f3559176f9a54191c810c48`; `codex_bridge.py` SHA-256 `22bd3b56b027e85cc89612419025ba5ebe6205dd8db3dc85102187c14e6deaa7`; `patching.py` SHA-256 `49cab7fad66ef8cf0bfcc3aa084a92d3579cab9d9104210e4ca8065d56461320`. Đây là fingerprint của các file được đối chiếu, không phải full runtime proof.
