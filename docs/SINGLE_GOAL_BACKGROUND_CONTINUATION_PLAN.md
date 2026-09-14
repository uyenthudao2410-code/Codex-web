# Kế hoạch: một Goal chạy nền, tự kiểm chứng và thực sự chạy bước tiếp theo

Ngày lập: 14/09/2026. Workspace được yêu cầu: `E:\DEV\Codex-web`.

**Trạng thái: gói kế hoạch và capsule để ChatWeb đăng ký Problem; chưa triển khai, chưa tạo canonical Problem hoặc cấp grant bởi tài liệu này.** Không coi mô tả action/field được đề xuất dưới đây là API đã tồn tại.

## 0. Cách giao gói này cho ChatWeb

Đọc file này cùng [JSON tạo Problem](problem-packets/single-goal-background-continuation.json). JSON là arguments của public `task_control`, không phải raw HTTP/JSON-RPC request, không chứa quyền/receipt/clock tự khai. Capsule tiếng Việt được rút gọn để giữ ngân sách bền vững 8 KiB; diễn giải đầy đủ ở tài liệu này.

Trình tự khi nhận yêu cầu người dùng:

1. Xác minh connector bind đúng endpoint/workspace. Đọc canonical Problem liên quan bằng public tools; không chọn Goal theo newest, timestamp hoặc vị trí trang.
2. Đối chiếu `prl-cc728c7fef2ba604633bf5d74ba87a1e` (no-manual-nudge) và `prl-e918c7d33e70c2d304d0797e11b05fcb` (continuity/telemetry), cùng state/revision hiện tại. Đây là ID quan sát trước, không phải current authority được thừa kế.
3. Nếu đây là mở rộng cùng vấn đề, ưu tiên `revise` Problem đúng phạm vi với `expected_revision`/`expected_contract_fingerprint` lấy từ kết quả mới. Dùng capsule BG01–BG14 nhưng giữ lịch sử/tiêu chí cũ có liên quan; không ghi đè âm thầm. Nếu phạm vi mới cần Problem riêng, giải thích quan hệ và dùng payload `open` đi kèm. Không mở lại pagination đã confirmed chỉ để có RUN mới.
4. Với `open`, payload cố ý không đặt `problem_id`: để server cấp ID. `event_id` là khóa idempotency của lần đăng ký này; retry cùng payload dùng cùng ID, thay nội dung phải dùng event/revision hợp lệ khác. Không tái dùng event `open` này làm `revise`.
5. Payload hợp schema không đồng nghĩa có authority. Nếu runtime thiếu attested host turn/controller hoặc tool schema phù hợp, báo typed blocker; không dùng raw localhost, fake identity hay direct SQLite để mở Problem.
6. Sau thành công, đọc lại exact Problem ID/revision/fingerprint/criteria và hiển thị checkpoint. Ghi những dữ liệu thực có sẵn qua producer hợp lệ; không fabricate failure đã được tái hiện, baseline hoặc consent.
7. Bắt đầu B0/B1 khi phạm vi yêu cầu cho phép. Live provider dispatch, tổng ngân sách nền, thay đổi quyền, restart, package/install và delivery phải có quyền riêng tương ứng. Việc tạo Problem không tự cấp tất cả các quyền đó.

**Thông điệp giao việc gợi ý:**

> Dùng `docs/SINGLE_GOAL_BACKGROUND_CONTINUATION_PLAN.md` và `docs/problem-packets/single-goal-background-continuation.json` để đăng ký đúng Problem cho một Goal chạy nền sau lượt ChatWeb, tự kiểm chứng và thực sự gọi bước tiếp theo, không bắt tôi chuyển tin giữa các chat. Trước khi mở mới hãy đối chiếu Problem no-manual-nudge và continuity hiện có để giữ lineage, không làm lại pagination đã đóng. Thu thập dữ liệu thật ngay từ B0: cả failure/replan, source, proof, acceptance và outcome hoặc missingness, qua canonical ledger hiện có. Sau đăng ký hãy read-back ID/revision/criteria và triển khai các bước đã có quyền; nếu thiếu scope, budget hoặc authority thật thì hỏi gọn đúng điểm thiếu. Không coi yêu cầu này là quyền tự cấp grant, paid dispatch, restart, commit/push/release hoặc tự xác nhận outcome.

## 1. Mục tiêu và giới hạn v1

Người dùng chọn một Goal, cấp phạm vi/ngân sách rõ ràng và bắt đầu một lần. Sau đó Coding MCP nhận kết quả worker, kiểm chứng tiêu chí, sinh yêu cầu có cấu trúc và thực sự dispatch lượt tiếp theo khi hợp lệ, kể cả khi response ChatWeb đã kết thúc. Người dùng không làm người chuyển báo cáo hoặc liên tục nhắn “tiếp tục”.

V1 giải quyết **intra-Goal continuation**, không tự chọn Goal mới trong backlog, không auto-accept và không ép tab ChatGPT.com tiếp tục sinh nội dung bằng browser automation. ChatWeb/controller hiện hữu giữ quyền semantic acceptance; executor nền nhận execution authority hẹp từ grant, không trở thành controller giả.

Các lần cần quyết định thật — đăng nhập, quyền mới, thay scope, tăng ngân sách, technical acceptance hoặc user outcome — vẫn hợp lệ. Đích là **zero manual relay, zero unnecessary nudge**, không phải zero human decision. Nếu đến ACCEPTING khi controller không có kênh gọi hợp lệ, v1 lưu review request và chờ; không hứa tự vượt boundary này. Nghiệm thu tự động nếu muốn là contract/packet riêng.

Máy sleep/tắt thì không làm việc. Worker hiện thuộc process MCP; process chết thì thread dừng. Durable state và Recovery Host chỉ cho phép phục hồi sau khi máy/runtime hoạt động lại với đúng quyền và identity; không có “daemon bất tử”.

## 2. Baseline và phần tái sử dụng

Git kiểm tra lúc lập gói: `main @ ae04947d5969e9ee92bf1fe7532bf30e186f8280`, nhiều source/test/docs/`.coding-tools` đang dirty do công việc đồng thời. Không thay base, clean, stage hoặc restart trong lượt lập kế hoạch. B0 phải thu identity/proof hiện hành, không lấy snapshot này làm authority lâu dài.

| Có sẵn | Nguồn | Dùng để làm gì |
| --- | --- | --- |
| Exact Goal identity, criteria/gap projection, bounded pagination | [goal_pursuit.py](../resources/coding-tools-mcp/coding_tools_mcp/goal_pursuit.py) | Đọc đúng Problem Revision; projection không cấp quyền |
| Continuation grant, action reservation, effect journal | [run_continuation.py](../resources/coding-tools-mcp/coding_tools_mcp/run_continuation.py) | Tái dùng RUN-local execution/proof bookkeeping |
| Worker thread, repair loop, auto-resume, STOP | [continuation_driver.py](../resources/coding-tools-mcp/coding_tools_mcp/continuation_driver.py) | Chạy ngoài request; không viết driver thứ hai |
| Giới hạn con 900 giây / 12 decision turns / 3 patch attempts | [continuation_contract.py](../resources/coding-tools-mcp/coding_tools_mcp/continuation_contract.py) | Giữ child bounds, bổ sung parent aggregate semantics |
| App Server launch/observe/events | [codex_bridge.py](../resources/coding-tools-mcp/coding_tools_mcp/codex_bridge.py) | Gửi thực và nhận kết quả; không chỉ tạo lời nhắc |
| Exact reattach/controller fencing | [controller_continuity.py](../resources/coding-tools-mcp/coding_tools_mcp/controller_continuity.py) | Phục hồi quyền theo guard, không giả client type |
| Typed events + summary trong canonical DB | [continuity_telemetry.py](../resources/coding-tools-mcp/coding_tools_mcp/continuity_telemetry.py) | Thu dữ liệu từ attempt đầu, không database thứ hai |
| Problem/outcome receipt | [problem_lineage.py](../resources/coding-tools-mcp/coding_tools_mcp/problem_lineage.py) | Technical/provisional/confirmed/reopen đúng loại |
| Lifecycle supervisor | [recoveryHost.js](../electron/services/recoveryHost.js) | Liveness/recovery, không cấp Goal authority |

API App Server có `thread/resume`, `turn/start` và notification `turn/completed`. Tích hợp phải probe schema/version thực tế của bridge, không tự giả định mọi field mới đều được bản cài hỗ trợ. Kênh này không chứng minh khả năng đánh thức tab ChatGPT.com. [OpenAI Docs: App Server](https://learn.chatgpt.com/docs/app-server)

Kế hoạch [BOOT_HOST_TRANSITION_CLOSURE_PLAN](BOOT_HOST_TRANSITION_CLOSURE_PLAN.md) sở hữu lỗi startup/epoch/deadline; kế hoạch [CONTINUATION_CLOSURE_PLAN](CONTINUATION_CLOSURE_PLAN.md) sở hữu nền continuation và evidence cũ. Chỉ nối dependencies/đóng gap liên quan, không làm lại cả hai chương trình hoặc coi chúng đã PASS.

## 3. Định nghĩa hoàn tất: BG01–BG14

Mã và summary trong JSON là nguồn cho capsule đăng ký. Diễn giải sau là oracle triển khai:

| ID | Điều phải chứng minh | Oracle / dữ liệu |
| --- | --- | --- |
| BG01 | Một exact Problem Revision/workspace/endpoint/owner; retry Start không tạo pursuit/RUN trùng | Concurrent-start và wrong-binding tests, unique durable identity |
| BG02 | ChatWeb response end không dừng công việc đã opt-in; explicit Stop/revoke phải dừng | Detached live case, stop race test, grant authority |
| BG03 | Kết quả thành PASS/FAIL/UNKNOWN từ proof/criteria thật | Oracle canary, missing/stale-evidence negative; model text không đóng Goal |
| BG04 | FAIL recoverable sinh typed proposal và thực sự dispatch/observe tiếp | Source-bound action → turn ID → result → proof, không human relay |
| BG05 | Budget parent bảo toàn qua child/restart, không reset ngầm | Atomic counters/reservations, exhaustion/cross-episode tests |
| BG06 | Duplicate/out-of-order event, lost response, unknown effect không lặp mutation | Fault injection + action idempotency và reconciliation receipt |
| BG07 | Reconnect/replacement revalidate source/epoch/authority, đúng máy | Exact rebind/revoke negatives và controlled recovery |
| BG08 | No-progress/expiry/authority drift/blocker thật dừng hữu hạn | Typed stop, no repeated unchanged attempts; Stop precedence |
| BG09 | Progress/review request ở cùng giao diện và đúng controller; ACCEPTING không auto-accept | Current controller review/reject flow, stale-review negative |
| BG10 | Công việc tự nhiên không cần copy giữa chat hoặc nudge thừa trong cửa sổ có quyền | Host/operator-observed interventions và independent live outcome |
| BG11 | Causal lineage đầy đủ cho cả failed/replanned attempt | Exact joins Problem/revision/RUN/WAVE/action/proof/checkpoint/outcome |
| BG12 | Dữ liệu idempotent, private, coverage rõ, synthetic riêng | Producer/consumer integration, duplicate identity, missingness tests |
| BG13 | Source/proof/acceptance/runtime exact, rollback không mất lịch sử | Focused + process proof, approved activation và migration rollback |
| BG14 | Confirmed chỉ khi đúng user outcome receipt; technical không thế outcome | Exact revision `reconcile_provisional`/`confirm` hoặc truthful `reopen` |

BG01–BG14 chưa được đo hay đạt bởi việc lập tài liệu. PASS v1 vẫn có thể kết thúc ở WAITING_REVIEW/WAITING_USER_OUTCOME đúng boundary; nhưng **không được gọi confirmed** trước BG14. Nút “đồng ý” có ý nghĩa không được đếm là manual relay; yêu cầu “copy báo cáo này sang chat kia” thì phải đếm.

## 4. Thiết kế vòng điều phối tối thiểu

```text
Explicit Goal + consent → durable parent grant + existing RUN binding
          → reserve child/action → App Server dispatch → observe result
          → exact oracle → PASS / FAIL / UNKNOWN
                  FAIL recoverable → typed proposal → validate → dispatch
                  UNKNOWN → bounded evidence/reconcile hoặc typed block
                  PASS → ACCEPTING → authorized controller review
                  remaining criteria after accepted work → next valid episode
                  final technical coverage → independent user outcome
```

### 4.1 Public surface và trạng thái

- Giữ đúng tám smart-v3 tools. Mở rộng bên trong `task_control`/Goal hoặc run-continuation action hiện có; tên cụ thể chốt B1, không copy tên giả từ kế hoạch như API đang tồn tại.
- `goal get/resolve` vẫn read-only. Start/consent là thao tác riêng explicit; `read` không tạo grant/RUN. Start trả durable handle và `completed=false` khi công việc còn chạy; RPC kết thúc không hủy Job.
- Trạng thái UI đề xuất: running, waiting_evidence, waiting_review, waiting_user, paused, blocked, complete. Đây là projection từ EOCL/grant/effect, không state machine cạnh tranh với ledger.
- `turn/completed` chỉ hoàn tất một model turn; không đủ đóng WAVE/Problem. Không spawn vì không thấy chữ trong chat hoặc timeout một tool card.
- Không dùng cron prompt. Nhận bridge events theo condition/queue hiện có và state transitions; watchdog timeout chỉ nhận diện mất tiến triển/liveness. Coalesce wake, một outstanding dispatch mỗi active child.

### 4.2 Parent grant và authority

Parent grant là **khả năng thực thi có phạm vi**, không phải quyền giả làm ChatWeb/controller. B1 phải xác định contract riêng cho background executor để có thể tiếp tục khi request ChatWeb kết thúc mà không cần duy trì một user turn giả.

Bind tối thiểu: Problem ID/revision/contract fingerprint; workspace/endpoint; issuer receipt; allowed paths/protected paths; allowed operations/oracles/provider route; parent expiry và tổng budget; stop/revoke policy; version và generation. Grant tạo bởi runtime sau explicit consent; model/user payload không tự khai `attestation_verified`, receipt, clock hay controller lease.

Execution lease của worker và quyền semantic accept là hai loại khác nhau. Không xóa check controller hiện có cho các call không được grant; implement internal child issuance chỉ khi exact parent grant còn hợp lệ và đã reserve budget. Mọi write vẫn đi EOCL/MCP/write lease. Sự kiện đã nhận không cấp quyền mới.

Giữ `controller_required` ở v1. Khi reviewer cần hoạt động, dùng đúng controller hoặc một delegation được cấp riêng bằng contract đã duyệt. Nếu không có kênh gọi controller được hỗ trợ, lưu review request và dừng đúng; không browser typing để đóng acceptance, không chuyển quyền theo nhãn model.

### 4.3 Budget và episode

Thông số khởi điểm để duyệt ở B1 (không phải quyền đã cấp): một Goal, một active child, parent tối đa 60 phút wall-clock, 4 episodes, 32 decision turns, 8 patch attempts. Child không vượt 900s/12/3 và chỉ nhận phần parent còn lại. Có thể chọn nhỏ hơn cho pilot; mọi thay đổi cần explicit consent trước khi phát grant.

Invariants kế toán:

- `consumed + reserved + available = authorized_total` cho từng tài nguyên đếm được; không âm, không vượt tổng.
- Parent reserve child allocation trong transaction trước dispatch. Child action consumption chuyển từ reserved sang consumed, không trừ hai lần. Trả unused reservation chỉ khi child/effect đã xác nhận terminal an toàn.
- Unknown dispatch/effect giữ reservation bảo thủ cho tới reconcile; không coi response mất là “chưa tốn” rồi phát grant mới.
- Parent absolute expiry không reset sau reconnect/restart/pause. Thời gian in-process dùng monotonic; reboot dùng expiry đã lưu/trusted clock. Clock không chắc chắn phải fail-closed; không biến rollback đồng hồ thành thêm quyền.
- Giới hạn tiền chỉ có thể enforce nếu có measurement/reservation giá hợp lệ; thiếu tiền/tokens là unknown. V1 luôn enforce lượt/patch/elapsed. Không hứa giới hạn USD bằng metric không đo được.
- Episode là đơn vị budget, không tự đồng nghĩa WAVE hoặc RUN mới. Reuse RUN; tạo WAVE chỉ khi EOCL yêu cầu do route/base/authority/attempt thay đổi. Không tự mở RUN mới để reset giới hạn hoặc tránh ACCEPTING.

Khi child hết budget mà parent còn: chỉ rotate nếu không pending effect, trạng thái EOCL cho phép, scope/oracle/source/authority vẫn hợp lệ, và chưa đến review/blocker thật. Parent không được auto-resume mọi trạng thái BLOCKED chỉ vì còn ngân sách.

### 4.4 Kiểm chứng và sinh yêu cầu tiếp theo

- Mỗi tiêu chí phải có oracle được controller chốt, inputs/fingerprint, loại evidence và mức cần người dùng. Nếu chỉ có mô tả mơ hồ, định vị thiếu bằng chứng; không tự chấm PASS bằng lời model.
- Bước tiếp theo là READ/PATCH/READY/BLOCKED theo proposal contract hiện có hoặc action deterministic đã cho phép. Không chạy free-form shell do nội dung log/tài liệu đề xuất.
- Packet gửi model chỉ có exact scope, lỗi/criterion chưa đạt, bằng chứng cần thiết, source/proof identity và remaining budget. Không replay toàn transcript, không scan toàn repo mỗi lượt.
- Chỉ gọi model khi cần phán đoán; quan sát status/so fingerprint/dedup/đếm budget dùng deterministic tools.
- Trước apply revalidate preimage/source và lease; sau apply proof external. Lưu failed attempt, không sửa test để làm xanh nếu test bảo vệ contract.

### 4.5 Crash, Stop và no-progress

- Lưu dispatch intent/action identity trước gọi provider; xử lý được event hoàn tất đến trước response, event trùng, response mất và event trễ. Nếu provider không hỗ trợ idempotent start, không tự phát lại unknown start; query/reconcile hoặc block.
- `daemon=True` hiện không sống qua MCP exit. Recovery Host chỉ rehydrate runtime; runtime mới xác minh grant, process/epoch/environment và pending effects trước tiếp tục. Runtime restart không tự gia hạn consent, không cross-machine failover.
- V1 có thể tiếp tục sau request ChatWeb kết thúc khi grant đã cho phép. User Stop/revoke phải thắng race trước dispatch tiếp theo và ngắt Job đang chạy theo cơ chế hỗ trợ. Interruption chưa rõ nguồn phải pause/reconcile; không coi mọi `interrupted` là provider failure để retry.
- No-progress threshold khởi điểm đề xuất: 3 decision attempts không có material evidence/proof/criterion tiến triển, không tính các heartbeat hay thời gian Job hợp lệ đang chạy. Hết threshold dừng và báo đúng chuỗi nguyên nhân; không có lỗi mới mà chỉ đổi lời mô tả không được tính là tiến triển.
- Tạm mất mạng/provider: bounded retry/backoff/circuit hiện có, không nhiều owner cùng thử. Mất credential, revoke, forbidden operation hoặc malformed authority không retry tự động.

## 5. Thu thập dữ liệu từ lúc tạo Problem, không đợi code xong

### 5.1 Hai tầng dữ liệu

1. **Dữ liệu của quá trình xây tính năng:** ChatWeb/EOCL ghi reproduction thật, READ/PATCH/proof, failure/replan, acceptance và kết quả. Bắt đầu ngay B0, kể cả khi background supervisor chưa có.
2. **Dữ liệu tính năng khi đã chạy:** producer runtime ghi dispatch/observe/rotation/budget/recovery/terminal theo schema được nghiệm thu. Không dùng kế hoạch làm bằng chứng tính năng đã chạy.

Canonical ledger là nguồn causal; task/performance/UI là projection. Tài liệu này và JSON capsule là hợp đồng, không nguồn ghi outcome. Không direct-edit `.coding-tools` để lấp metric hoặc tạo database song song.

### 5.2 Mapping vào telemetry đang có

| Sự kiện cần thu | Event hiện hữu dùng được | Link/counter/điểm chú ý |
| --- | --- | --- |
| Người dùng nhắc tiếp tục | `manual_nudge` | Chỉ khi host/operator quan sát thật; vắng row không tự nghĩa zero |
| Boundary bị ngắt, report chờ | `interruption`, `report_gate` | Phân biệt response end bình thường và stall thật |
| Attempt và kết quả | `continuation_attempt`, `continuation_success`, `continuation_failure` | Gắn exact logical ID, RUN/WAVE, outcome/code; success một lượt không phải Goal success |
| Sửa chiến lược | `replan` | Có cause và evidence thay đổi; không xóa attempt trước |
| Kết nối/phục hồi | `reconnect`, `restart`, `resume` | Exact old/new correlation qua receipt; không suy ra từ thời gian gần nhau |
| Ngăn replay | `duplicate_effect_prevented` | Giữ action identity và trạng thái pending; không tự tuyên bố effect chưa xảy ra |
| Kết thúc/chặn/nghiệm thu | `terminal`, `blocker`, `accepted_checkpoint` | Outcome/reason đúng loại; confirmed dùng PRL independent receipt |

Các event/counter mới như parent grant, episode reserve/release, manual relay, no-progress và delivered review không nằm đầy đủ trong allowlist hiện tại. B2 phải định nghĩa typed producer/consumer và migration tối thiểu trước khi ghi. Không gửi arbitrary JSON hoặc enum mới vào tool cũ. “Event-only” không đủ cho mutation/budget authority: reservation và pending-effect là durable authoritative state; projection chỉ để quan sát.

### 5.3 Trường và measurement contract

- Identity runtime-derived: Problem/revision, RUN/WAVE, goal execution/episode/action, task context, process/server/epoch, opaque endpoint/workspace generation, source/checkpoint/proof identity.
- Operation facts: event type, status, typed cause, oracle result, count/budget reservation-consumption, timestamps/duration có clock source, retry/recovery result. Không có raw prompt/transcript/private reasoning.
- Phân biệt `work_origin`: engineering implementation của tính năng, synthetic fault canary, natural pilot. Tái dùng provenance contract đang có; không tự nhận representative để tăng mẫu.
- Metrics: manual relay count; unnecessary nudge count; auto-dispatch success; time from verified completion to next dispatch; time-to-accepted/outcome; no-progress stops; duplicate-effect prevention; remaining/consumed budget; sample/coverage theo cửa sổ.
- Mỗi metric công bố numerator, denominator, window, observation source, known/unknown. Lượt không được instrument không được điền zero; không tính chỉ các RUN accepted rồi bỏ failures hoặc trường hợp missing.
- `manual_relay_count=0` trong pilot cần host-observed receipt hoặc operator xác nhận rõ cửa sổ, không suy ra từ không thấy text. Phiên bản đầu có thể dùng explicit operator observation được đánh dấu đúng nguồn; không cần đọc nội dung clipboard hoặc theo dõi mọi chat.
- Phân biệt legitimate approval/outcome với unnecessary nudge. Rejected hoặc blocked vẫn nằm trong báo cáo; không dùng lượng event hoặc việc người dùng đồng ý rank để kết luận lợi ích causal/ROI.

Privacy/retention: chỉ opaque IDs và bounded codes; không cookie, key, Authorization header, credentials, HR data hoặc tên người. Dedup bằng logical identity, không timestamp trùng. Không tự prune `.coding-tools`; retention theo AGENTS. Telemetry analytics lỗi phải báo coverage thiếu; nếu durable budget/effect write lỗi thì không dispatch mutation mới.

## 6. Kế hoạch B0–B7 và ownership

| Gói | Nội dung / output | Phụ thuộc | Owner / giới hạn |
| --- | --- | --- | --- |
| B0 | Exact Problem/revision, overlap decision, baseline, source ownership, oracle và dữ liệu ban đầu | Không | Controller; canonical actions, không direct DB |
| B1 | Chốt parent grant, episode/budget/STOP, public schema và authority semantics | B0 | Controller giữ trust decisions; contract tests trước production |
| B2 | Causal instrumentation và reporter tối thiểu, trước runtime loop | B0, interface B1 | Một telemetry owner, read-only reporter; dùng ledger hiện có |
| B3 | Parent grant/reservation, child issuance/rotation và fail-closed migration | B1; producer B2 | Một writer phạm vi grant/ledger; không auto-accept |
| B4 | Event → oracle → typed next proposal → actual dispatch, không human relay | B3 | Một continuation writer; bridge dùng lại |
| B5 | Recovery/no-progress/Stop + một giao diện nhận review và kết quả | B2–B4 | Controller tích hợp; không giả online ChatWeb |
| B6 | Focused/integrated/process/live proof, source acceptance và natural pilot | B0–B5 | Controller + proof plane + operator đúng quyền |
| B7 | Đối chiếu criteria, outcome, delivery và closure | B6 | Exact semantic controller; user outcome độc lập |

Đường chính `B0 → B1 → B3 → B4 → B5 → B6 → B7`; B2 là dependency dữ liệu phải sẵn sàng trước ca thực thi đầu tiên, không để tới cuối. Sau B1, B2 và candidate B3 có thể chạy song song ở phạm vi không chồng; khi shared ledger schema/controller/driver bị giao nhau, tích hợp tuần tự bởi một owner.

Không đồng thời sửa source authoritative giữa nhiều worker. Nếu dùng candidate/worktree, worktree ngoài `.coding-tools`; proof/adoption phải bind đúng integrated bytes. Module budget theo AGENTS: không dồn hết vào `server.py`/`orchestration_ledger.py`; chỉ tách một module Goal-execution nhỏ nếu trách nhiệm mới cần, không framework đa Goal.

### B0 — Tạo đúng Problem và ghi baseline thật

- Thực hiện mục 0. Không mặc nhiên chọn mới hoặc sửa Problem cũ chỉ theo tên. Giữ pagination confirmed và boot-recovery dependency riêng.
- Thu HEAD/dirty manifest, active RUN/WAVE/lease/jobs và exact runtime-loaded source. File dirty thuộc writer khác phải được giữ; không tranh quyền bằng local script.
- Đăng ký oracle BG01–BG14 và measurement window trước canary. Thu baseline/manual-relay quan sát được; thiếu thì unknown. Không dựng historical baseline sau khi feature đã chạy.
- Chốt quyền development source/proof riêng với quyền background operation, provider cost, activation, install và delivery. Thiếu thì checkpoint BLOCKED đúng mục, các read-only packet khác vẫn có thể chuẩn bị.

Exit B0: server read-back Problem/revision/fingerprint, criteria và mapped dependencies, route/owner/lease đúng scope. Tạo Problem thành công không đồng nghĩa grant đã issued hoặc driver đang chạy.

### B1 — Settled contract trước code

- Viết failing fixtures cho exact binding, repeated Start, no grant, expired/revoked grant, policy drift, parent counters và ACCEPTING không auto-accept.
- Chốt request/response schema cho start/get/pause/resume/stop trong tool hiện có; các action name chỉ được sử dụng sau khi current server và client đều công bố.
- Thiết kế background execution capability hợp lệ khi ChatWeb response đã kết thúc. Không dùng renew ChatWeb lease giả làm giải pháp; public caller vẫn phải có controller authority theo contract.
- Chốt reporter fields và budget/cursor/event IDs với B2. Input source/oracle allowlist và protected test hash là phần grant; model không tự thêm check tốn chi phí hoặc path ngoài scope.
- Public contract delta phải diff, phân loại additive/breaking và có exact-SHA regression/activation plan. Không thêm hash để né real discovery.

Exit B1: các decision về quyền, budget, child rotation, privacy và review đã rõ; không còn giả định “caller đọc đúng schema thì có quyền”.

### B2 — Telemetry-first đúng giới hạn

- Dùng valid event types mục 5.2 cho tiến trình sửa ngay khi có runtime producer tương ứng. Parent/episode fields mới đi migration/API nội bộ được kiểm chứng, không arbitrary payload.
- Producer và read-only consumer dùng chung definition; test real producer output vào reporter để tránh AVAILABLE/OBSERVED hoặc rate/coverage mismatch cũ.
- Verify retry logical-ID idempotence, conflict detection khi cùng ID khác facts, missing denominator và counter bounds, privacy rejection, failure before commit/after event persisted.
- Không cần lớp xếp hạng, economics predictor hay policy optimizer trong gói này; reporter phải trả dữ liệu mô tả và missingness đủ để đánh giá.

Exit B2: reconstruct một synthetic journey từ rows/receipts mà không transcript; duplicates không đếm hai lần, dữ liệu thiếu không thành zero; proof không cấp mutation authority.

### B3 — Parent grant và atomic accounting

- Extend mixin/ledger domain hiện có cho parent grant và episode records trong cùng canonical DB khi thật sự cần. One-active-owner uniqueness theo exact Goal execution, giữ run mapping; migration backward-compatible/fail-closed.
- Atomically reserve episode, issue bound child grant, cập nhật counters và idempotency trước dispatch. Tách policy issued với execution started, observed và terminal.
- Migration bảo toàn grant cũ như RUN-local; không tự nâng mọi old grant thành parent consent, không reset usage lịch sử.
- Test child cap, parent cap, crash giữa reserve/issue, retry cùng event, revoke race, clock skew, stale owner fencing, unused budget refund đúng điều kiện và unknown effect không refund.

Exit B3: phương trình budget mục 4.3 giữ trong concurrent/fault tests, bất kỳ grant thiếu authority không tạo child, không cần user message mới cho rotation đã được cấp trong parent.

### B4 — Nối vòng thực thi

- Reuse driver/bridge hiện có; một durable execution handle cho UI. Khi nhận event, revalidate exact Job và consume qua cursor/idempotent action; không bắt model scan repo lại.
- Oracle success/known failure/unknown xác định nhánh. READ/PATCH ngoài scope bị từ chối; READY không tự checkpoint; BLOCKED có typed reason và missing evidence.
- Child budget exhausted eligible thì rotate đúng parent; report gate/REPLAN chỉ resume khi transition hợp lệ, không blanket skip ACK hay acceptance.
- Ghi đủ planned/reserved/dispatched/observed/proved facts. Bridge start trả unknown thì giữ pending và reconcile; không phát lại vì HTTP tool card bị timeout.

Exit B4: isolated case tự đi từ READ → PATCH → proof fail → repair → proof pass → ACCEPTING mà user không phải chuyển tin, tất cả writes do MCP và exact lease.

### B5 — Giao diện, recovery và STOP

- ChatWeb vẫn nơi giao việc/review; khi mở lại, đọc bound Goal execution handle để hiện đúng status. App panel có thể hiển thị progress/request và nút mở đúng controller view, nhưng thao tác này không tự đánh thức model.
- Cần action trực tiếp tại panel thì phải dùng authenticated adapter đúng contract, revalidate checkpoint/hash/owner. Nếu chưa có adapter nghiệm thu hợp lệ, thông báo rõ và chỉ hỗ trợ quyết định từ controller thật; không tuyên bố zero-relay closure cho flow vẫn cần dán báo cáo.
- Worker/reviewer results tự được hệ thống chuyển, không phải operator copy. BG09 được kiểm chứng ở giao diện thực, không chỉ bằng queue row.
- No-progress/circuit, explicit pause/revoke/Stop và restart recovery theo mục 4.5. User Stop được lưu đủ bền để MCP reboot không chạy lại trái ý.
- Recovery Host chỉ giám sát process/lifecycle; dùng dependency boot plan cho epoch mới. Không buộc rollout hai máy nếu scope v1 một endpoint, nhưng luôn test wrong-endpoint negative; multi-machine live là gate boot program riêng.

Exit B5: frontend reload không làm mất handle, Stop thắng dispatch mới, review evidence tự về đúng nơi; process restart không lặp effect; không còn claim “backend tự accept vì chat im”.

### B6 — Proof và pilot theo lớp

1. Chạy focused tests khi source liên quan đổi; integration theo danh sách mục 7. Proof cache chỉ reuse exact inputs.
2. Cho controller accept exact integrated file receipts qua EOCL. Với WIP cũ, dùng supported adoption và giữ lịch sử failed attempts; không “test xanh = đã durable accepted”.
3. Controlled activation chỉ khi có authority và fresh census không chặn. Xác minh source loaded/epoch/process đúng; source trên đĩa không thay live proof. Không restart active jobs để chạy canary.
4. Synthetic detached canary và fault injection ở workspace/profile cô lập, budget nhỏ, test bảo vệ immutable. Thử chat response end, parent rotation, Stop, timeout/lost-response và restore. Không gọi chúng là natural outcome.
5. Một pilot tự nhiên đúng Problem hiện có, oracle và ngân sách đã chốt. Trong cửa sổ quan sát, user không gửi nudge thừa hoặc relay; nếu không có event thiếu budget thực thì không cưỡng ép natural failure, dùng synthetic test cho branch đó.
6. Giữ fail/retry/blocked samples và coverage. Muốn đánh giá hiệu quả rộng hơn, thu 5–10 phiên tự nhiên sau pilot; đó là calibration mô tả, không mẫu đủ tự kết luận causal gain/ROI.

Exit B6: BG01–BG13 có evidence tương ứng; live detached continuation dùng thật, không đọc lại log rồi nói “chắc đã chạy”. Thiếu machine/provider/controller access thì NOT_RUN và giữ gate mở.

### B7 — Thu outcome và chốt

- Exact Problem/revision không thay. Technical acceptance chỉ đi provisional qua `reconcile_provisional` và checkpoint guard khi phù hợp.
- Chỉ `confirm` khi explicit user outcome của đúng revision được runtime ghi receipt. Không tự viết `outcome_receipt_id`, không dùng executor statement thay lời người dùng.
- Cùng lỗi vẫn xảy ra → `reopen`; thay requirement thật → `revise`; không tạo Problem mới mỗi retry để mất recurrence. Giải quyết attempt ownership/terminality cần thiết, nhưng không terminalize mọi RUN khác của workspace.
- Completion report nêu proof, cost/coverage missing, manual relay/nudge, còn pending gì, Git/runtime/artifact status và quyền nào đã dùng. ACK report bằng exact ID nếu workflow yêu cầu.
- Delivery riêng: trước mỗi commit/push có quyền, `npm run stage:coding-tools-delivery` rồi `npm run check:coding-tools-delivery`, giữ toàn bộ evidence trừ đúng hai SQLite sidecar theo AGENTS. Không bypass secret conflict. Package/release/install chỉ khi được giao, không ngầm kèm theo confirmed resolution.

Exit B7: BG14 được chứng minh và server transition đúng; không còn blocker bắt buộc. Nếu chỉ technical/canary đạt thì nói đúng mức, không khép toàn bộ.

## 7. Test lanes và ma trận thử nghiệm

Lệnh bên dưới là kế hoạch, chưa được thực hiện bởi việc lập file. Chạy Python từ `resources/coding-tools-mcp`, Node từ repo root; thêm case vào suite chủ sở hữu, chỉ thêm file mới khi có lý do cụ thể.

| Phạm vi | Suite hiện có |
| --- | --- |
| Exact identity/criteria/cursor | `tests/test_goal_pursuit.py` |
| Grant/reserve/driver/rotation/recovery | `tests/test_run_continuation.py` |
| Reattach/knowledge/controller | `tests/test_controller_continuity.py` |
| Consent web/local + missing authority | `tests/test_continuation_consent_http.py`, `tests/test_problem_lineage.py` |
| Bridge start/events/unknown/timeout | `tests/test_codex_bridge.py` |
| Typed telemetry/reporters | `tests/test_continuity_telemetry.py` và consumer suite bị thay đổi |
| Exact file acceptance + proof surface | `tests/test_acceptance_file_attestation.py`, `tests/test_orchestration_workflow.py` |
| Lifecycle + panel binding | Node `tests/recovery-host.test.js`, `tests/runtime-lifecycle.test.js`, `tests/connector-binding.test.js` và UI suite tương ứng |
| Process boundary | `npm run test:recovery:e2e` + isolated continuation case nếu fixture hiện tại chưa bao phủ |

Public schema thay đổi cần contract/hash tests và client-discovery plan. Integrated gate `npm run test:all` chỉ tại exact candidate hoặc khi cross-boundary cần; không full suite mỗi lượt. Không live provider call để kiểm tra một phép tính budget; mock/fake clock trước.

| Ca | Kịch bản | Kết quả mong đợi |
| --- | --- | --- |
| T01 | Hai request Start cùng idempotency/Goal | Một durable pursuit và một active child, handle ổn định |
| T02 | Response ChatWeb hoàn tất trong lúc worker có quyền chạy | Worker tiếp tục; không user message, `start/resume` hoặc lời gọi quan sát có side effect kích hoạt thêm trong detached window |
| T03 | FAIL proof recoverable | Typed repair proposal → validated patch → proof mới, giữ lỗi cũ |
| T04 | Oracle thiếu hoặc evidence stale | UNKNOWN → đọc bổ sung hữu hạn/reconcile/block; không auto PASS |
| T05 | Child hết budget, parent còn | Đợt mới dùng đúng reservation, không reset tổng, không duplicate RUN |
| T06 | Parent hết hoặc revoked/expired | Không dispatch mới; đúng stop/review state, không gia hạn |
| T07 | Completion event trùng/out-of-order, event trước response | Consume idempotent, final state không lùi về inProgress |
| T08 | Provider start có thể đã chạy nhưng response mất | Reconcile exact identity hoặc block; không tự replay |
| T09 | MCP restart giữa effect prepared/applied/proved | Giữ journal/reservation; no duplicate mutation; rebind đúng quyền |
| T10 | Source/Problem revision/controller/endpoint đổi | Stale capability bị chặn; không copy quyền sang đích mới |
| T11 | Explicit Stop đồng thời wake/dispatch | Stop/revoke bền vững và không post-stop dispatch; job hiện hữu cancel theo contract |
| T12 | No-progress 3 attempts, nhưng Job đang chạy không bị tính sai | Circuit hữu hạn; không stop chỉ vì model lâu hoặc không có text |
| T13 | ACCEPTING trong lúc chat không active | Review request được lưu/hiện đúng; không self-accept; controller review bằng exact evidence |
| T14 | Telemetry duplicate/missing/invalid/private data | Không double count; unknown có coverage; input nhạy cảm bị từ chối |
| T15 | Migration/rollback và grant cũ | Không nâng quyền grant cũ, không drop ledger/events hay reset budget |
| T16 | Pilot một Goal tự nhiên từ giao một lần đến kết quả | Zero manual relay/unnecessary nudge được quan sát, BG14 là outcome thật |

Minimum đề xuất: T01–T15 có discriminating automated cases; T02/T05/T08/T09/T11 có isolated real-process proof; T16 ít nhất một ca tự nhiên và xác nhận độc lập. Repeated polls không phải samples; thiếu quyền fault injection/provider thì giữ NOT_RUN. Không khẳng định độ tin cậy dài hạn từ một pilot.

## 8. Rollback, reporting và tiêu chí dừng chương trình

- Default-off cho parent-goal execution mới tới khi B1/B6 đạt. Existing RUN-only continuation không bị tự nâng cấp; reader phiên bản cũ gặp grant version mới phải fail-closed, không reset nó.
- Trước migration lấy transactionally consistent snapshot đúng cơ chế repo và kiểm tra restoration ở fixture. Rollback code không đồng nghĩa copy đè ledger cũ: giữ event mới, schema compatibility và pending grants; nếu không thể downgrade an toàn, disable new feature và sửa forward.
- Stop triển khai mutation khi thiếu lease/authority, wrong workspace, unknown effect, source drift, provider cost chưa được cấp, secret trong evidence hoặc concurrent owner chưa giải quyết. Không dùng heartbeat tự nhắc để che blocker.
- Mỗi WAVE/batch: báo đã làm gì, state Git/RUN/WAVE/runtime, strongest proof, typed blocker, remaining work và exact next action. Khi dừng, report người dùng nhìn thấy là bắt buộc; tool output đơn độc không đủ.
- Engineering progression phải tối ưu accepted result/operator burden; nếu việc bổ sung lớp mới tốn hơn relay đã đo và không cải thiện workflow, thu hẹp/REMOVE phần thừa. Không đánh đổi safety/correctness để giảm số câu hỏi.

## 9. Deliverables và hành động đầu tiên

Deliverables: canonical Problem Revision; B1 contract + discriminating tests; code/proof accepted đúng bytes; event/metric schema và reporter có coverage; live detached no-relay evidence; recovery/Stop proof; user outcome hoặc exact missingness; completion report. Tài liệu và JSON hiện tại chỉ là đầu vào, không thay các deliverables đó.

Việc ChatWeb cần làm ngay sau khi được giao gói: **B0 read-back/dedup/create-or-revise và bắt đầu thu bằng chứng hiện có**. Sau đó B1/B2 trước B3/B4. Không yêu cầu người dùng copy lại output giữa các chat trong từng WAVE; controller đọc Job/Problem evidence trực tiếp. Trong quá trình xây tính năng, nếu chính kênh điều phối đang thiếu thì ghi limitation thật và dùng một controller được chỉ định với công cụ giao việc được hỗ trợ, không hứa tính năng chưa có đã hoạt động.

Đích nghiệm thu cuối: **một yêu cầu ban đầu có quyền rõ ràng, hệ thống tự nhận kết quả và thực sự chạy bước tiếp theo cho cùng Goal sau khi lượt ChatWeb kết thúc; người dùng chỉ còn quyết định thực sự cần thiết và xác nhận outcome, không làm người chuyển tin. Mọi lần sửa đồng thời tạo thêm dữ liệu có provenance, không tạo thêm sự thật giả.**
