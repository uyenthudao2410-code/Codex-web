# Đánh giá khả thi: công việc bền vững vượt qua vòng đời chat turn

Ngày nghiên cứu: **07/09/2026**. Phạm vi: Windows Electron Execution Hub + Coding Tools MCP tại `E:\DEV\Codex-web`, đối chiếu tư vấn đính kèm về Durable Agent / AgentTask / TaskAttempt / Wake Intent.

Trạng thái tài liệu: **nghiên cứu để ra quyết định, chưa phải thiết kế được duyệt hay biên bản triển khai**. Không sửa source sản phẩm, không migrate ledger, không mở workload/agent thực, không restart, commit, push, publish, release hoặc deploy. Đây là tài liệu mới; các nghiên cứu có niên đại trước đó được giữ nguyên.

## 1. Kết luận điều hành

**Khả thi và có giá trị, nhưng không nên triển khai nguyên xi đề xuất “port toàn bộ Durable Agent runtime của upstream trước”.**

Hướng phù hợp hơn là đóng khoảng trống nối tiếp trên cơ chế hiện có, đồng thời chứng minh host nào thực sự có quyền khởi động bước suy luận tiếp theo. Có ba kết luận riêng:

1. **Giữ mục tiêu, checkpoint, proof và identity qua chat/session: khả thi cao, dự án đã có nền tảng và một phần cơ chế hoạt động.** Không chỉ có oracle/report: code đã có knowledge checkpoint, ACK, reattach có transaction và chuyển controller lease/fencing.
2. **Tiếp tục quan sát một Job khi browser/transport mất kết nối: khả thi có điều kiện.** Phải phân biệt process owner còn sống với restart chính process owner. Đường Windows hiện tại có kill-on-close; không được hứa Job sống qua mọi restart chỉ vì metadata được persist.
3. **Tự suy luận tiếp khi ordinary ChatGPT chat không còn turn: chưa được chứng minh cho connector hiện tại.** Tuy nhiên, không thể mở rộng kết luận thành “OpenAI không có cơ chế chính thức nào”: tài liệu hiện có UI follow-up bridge, host long-running Work, và Workspace Agents API để trigger một published agent. Mỗi đường có boundary và điều kiện riêng, không phải quyền tự resume mọi chat thông thường. [OpenAI UI reference](https://developers.openai.com/plugins/reference), [long-running work](https://learn.chatgpt.com/docs/long-running-work), [Workspace Agents trigger API](https://learn.chatgpt.com/workspace-agents/trigger-runs).

| Kỳ vọng của người dùng | Đánh giá | Điều kiện phải chứng minh |
|---|---|---|
| Mở session mới, nhận lại đúng công việc và bằng chứng | Nên ưu tiên, phần lớn nền tảng đã có | Exact workspace / Problem Revision / role / checkpoint / lease; không chọn task bằng “gần nhất” |
| Không chạy lại test/build đang chạy chỉ vì turn cũ mất | Khả thi trong lifetime của executor | Job ID và observation cursor bền vững; effect receipt; không suy từ PID đơn lẻ |
| Restart Coding MCP rồi tiếp tục cùng process | Chưa thể hứa ở đường Windows hiện tại | Hợp đồng process-owner, output và recovery phải được chứng minh riêng |
| Browser mở, widget xin host gửi follow-up | Có API chính thức để nghiên cứu | Host hỗ trợ, UI còn hoạt động, quyền rõ ràng, chống gửi trùng; chưa có pilot tại dự án |
| Browser đóng, model vẫn sửa → test → sửa tiếp | Có đường kỹ thuật nếu host/executor sở hữu inference loop | Host Work/Codex hoặc API adapter được cấp quyền; không chỉ thêm một bảng Wake |
| Giữ ordinary chat hiện tại và server tự mở turn tùy ý | Không cam kết trên bằng chứng hiện có | Cần capability/adapter chính thức được kiểm chứng trên đúng host và account |

**Quyết định đề xuất:** GO cho một spike tích hợp hẹp sau khi được duyệt; NO-GO cho wholesale port hoặc lời hứa “giống Codex Desktop hoàn toàn” trước khi qua host-continuation gate.

## 2. Phương pháp và đường biên bằng chứng

- Baseline được kiểm tra trực tiếp: branch `main`, HEAD `58dfd3093d7a05f6999fe93e15c94050aa51d204`, đúng commit tư vấn đề cập.
- Checkout không sạch. Có WIP sẵn ở dashboard, `coordination.py`, `problem_lineage_activation.py`, `restart_ticket.py` và các tests liên quan; `.coding-tools` tiếp tục có biến động. Kết luận source là về working tree được quan sát, không giả định mọi byte đều là committed HEAD hoặc đã được runtime nạp.
- Thứ tự ưu tiên: code/focused tests → current product contract → maintained docs → tư vấn/dated research. `docs/CURRENT_STATE.md:7` và `docs/ROADMAP.md:5` yêu cầu hội tụ, không thêm control plane chỉ vì upstream có một lớp mới.
- Dùng hai nhánh rà soát chỉ đọc độc lập cho Python continuity và Rust/upstream. Kết luận và phạm vi do task chính quyết định. Preflight native worker sẵn sàng; không dùng kết quả preflight để khẳng định model identity của controller hoặc chi phí provider.
- Phiên này không có public Coding Tools MCP callable surface; dùng shell đọc source và những reporter/query-only reader có sẵn. Không tự tạo EOCL RUN/WAVE, không gọi acceptance/audit có tác dụng ghi, không coi kết quả nghiên cứu là `EOCL_ACCEPTED`.
- Ledger được đọc qua Backup API snapshot và query-only reader, không khởi tạo canonical writer. Các snapshot khác thời điểm không được trộn thành một transaction.
- Mười hai focused tests chạy trên fixture/mock; không có thử nghiệm ngắt browser, restart service, provider inference hay triển khai thật. `FOCUSED_PROOF` không phải `LIVE`, `PACKAGED_RELEASED` hoặc natural outcome.

## 3. Những nhận định trong tư vấn cần giữ hoặc sửa

| Nhận định | Kết quả đối chiếu |
|---|---|
| Không đồng nhất model context, task state và runtime state | Đúng hướng; phù hợp kiến trúc hiện có |
| `cross_session_continuity_report.py` là oracle, không tạo journey | Đúng; docstring và `_policy()` xác nhận điều này |
| Dự án chỉ biết đo continuity, chưa có cơ chế reattach/ownership | Quá rộng: `controller_continuity.py` đã có reattach transaction, generation và transfer lease/fencing |
| Thiếu chính tên `AgentTask`/`TaskAttempt` thì phải nhập thêm model đó | Không đủ cơ sở: tên khác không chứng minh thiếu semantics; Problem Revision/RUN/WAVE đã sở hữu nhiều trách nhiệm tương ứng |
| Process dài có thể sống ngoài chat turn | Đúng có điều kiện; chưa suy ra sống ngoài process owner hoặc qua full-clean restart |
| Upstream đã có durable Task/Attempt và Wake | Đúng ở source được pin; A3 ownership không đồng nghĩa backend dispatch, và fake adapter không phải production ChatGPT wake |
| Bootstrap nhận ra task chưa terminal thì không cần người dùng kích hoạt gì | Thiếu tiền đề: bootstrap chỉ chạy khi host thực sự thực thi một request/turn hoặc adapter có trigger |
| Có Wake Intent là gần như tự tiếp tục được | Chưa đủ: intent chỉ là công việc cần giao; phải có consumer có quyền gọi model, budget và admission |
| Test pass → `ACCEPTED` là hoàn tất Goal | Không khớp đầy đủ PRL hiện tại: technical acceptance khác independent user outcome; cần giữ provisional/confirmed/reopen |
| Không nên thêm Goal Engine/control plane song song | Đồng ý và là ràng buộc thiết kế chính |
| Đây là ưu tiên lớn nhất, hơn mọi tối ưu khác | Chưa chứng minh được về kinh tế: chưa có dữ liệu đủ để quy kết operator burden/TTAR cho đứt turn là nguyên nhân chi phối |

Tài liệu chính thức xác nhận Work phục vụ hosted long-running work, nhưng nghiên cứu này không dùng mốc quảng bá “ra mắt tháng 7/2026” hay mô tả năng lực tuyệt đối để quyết định kiến trúc. Cũng không xác nhận account hiện tại có đầy đủ các chức năng được mô tả. [OpenAI long-running work](https://learn.chatgpt.com/docs/long-running-work).

## 4. Dự án đã có gì có thể tái sử dụng?

Các đường dẫn đầy đủ bên dưới tính từ root repository. Tên module Python viết gọn nằm trong `resources/coding-tools-mcp/coding_tools_mcp/`; các Python test tương ứng nằm trong `resources/coding-tools-mcp/tests/`. Số dòng là vị trí quan sát trong working tree ngày nghiên cứu.

| Trách nhiệm | Bằng chứng hiện có | Kết luận |
|---|---|---|
| Mục tiêu của người dùng độc lập với attempts | `docs/ARCHITECTURE.md:41`, `problem_lineage.py`, `resolution_contract.py` | KEEP Problem Revision; không thêm bản sao Goal có terminal semantics khác |
| Attempts và bằng chứng kỹ thuật | `orchestration_ledger.py`; bảng `runs`, `waves`, `proofs`, `checkpoints` | KEEP ledger/EOCL làm authority; TaskAttempt nếu cần chỉ là mapping rõ ràng, không writer/lease thứ hai |
| Knowledge checkpoint và recovery delta | `controller_continuity.py:705`, `:845` | Có ACK phân loại CURRENT/BEHIND/MISSING/FUTURE/HISTORY_LOST; ACK tự nó không cấp quyền |
| Reattach có thực thi state transition | `controller_continuity.py:478`, `:597`, `:654` | Có transaction, exact Problem Revision/ACK/client, generation, lease transfer và replay idempotency |
| Context capsule bounded | `controller_continuity.py:1035`, `:1138` | Continuity Core tối đa 8 KiB; source/runtime freshness; không tự cấp mutation/acceptance authority |
| Public integration seam | `coordination.py:1089` | `task_control(action="continuity")` đã có; không cần tool thứ chín |
| Durable job accounting / ownership | `execution_resources.py:1018`, bảng `managed_process_jobs` | Có reconciliation; handle/identity không khớp có thể thành orphaned/quiesced, không nhận bừa process |
| Background tool operation | `runtime_background.py:26`, `server.py:422` | Handle trong ledger, execution/result thuộc MCP process; khai báo rõ `restart_safe=false` |
| Pending-message/handoff substrate | `orchestration_ledger.py:492`, `:510` | Có `coordination_messages` và `handoff_capsules`; ứng viên reuse, chưa phải wake delivery contract |
| Live command session | `server.py:376`, `processes.py:345`, `exec_tools.py:350` | Process handle/readers/session có phần trong memory; persistence của bảng Job không khôi phục chúng một cách kỳ diệu |
| Persistent model lane | `codex_bridge.py:671`; `tests/test_codex_bridge.py:119` | Đã có `thread/read` → `thread/resume` → `turn/start` với workspace/session guard; đây là Codex lane, không phải resume ChatGPT ordinary chat |
| Oracle end-to-end | `cross_session_continuity_report.py:1`, `:364`, `:382` | KEEP làm bằng chứng kiểm chứng; không biến reporter thành scheduler |

Một khác biệt đặc biệt quan trọng: code reattach có thể chuyển lease sau khi các guard hợp lệ, còn checkpoint/ACK/capsule không tự cấp quyền. Không được gom toàn bộ continuity thành “chỉ read-only” hoặc ngược lại coi có checkpoint là đủ authority để resume.

### 4.1. Giới hạn process trên Windows

`processes.py:126` gắn process vào Windows Job Object với `KILL_ON_JOB_CLOSE`; handle thuộc process đang quản lý. `server.py:376` giữ exec sessions trong memory. `execution_resources.py:1018` xử lý process owner/handle mất bằng reconciliation; test `test_restart_marks_live_owner_orphaned_and_blocks_heavy` tại `tests/test_execution_resources.py:655` mô tả refusal `UNOWNED_EXECUTION_PROCESS`.

Vì vậy phải tách ít nhất bốn failure domains:

1. Chat/model turn kết thúc nhưng Coding MCP và executor còn sống.
2. Browser/transport mất rồi quay lại, process owner vẫn sống.
3. Coding MCP/process owner restart; control metadata còn nhưng handles/readers có thể mất và child có thể bị kết thúc.
4. Máy hoặc executor restart; cùng OS process không thể được bảo toàn chỉ bằng ledger.

Không được tắt kill-on-close, nhận PID sống hoặc chuyển mọi process sang detached để làm demo pass. Nếu nghiệp vụ thật sự cần case 3, phải xác định owner sống độc lập, durable stdout/stderr/exit receipt và explicit recovery contract. Nếu owner đã chết, ghi nhận interrupted/lost/unknown theo semantics được duyệt; chỉ retry khi có bằng chứng an toàn, không giả là cùng Job tiếp tục.

`runtime_background.py:26` còn khai báo trực tiếp `card_or_transport_loss=survive`, `same_process_reconnect=survive`, `mcp_process_restart=reconcile_or_orphan`, `recovery_host_replacement=lost_or_orphan`. Source contract này phù hợp với sự phân biệt ở trên; một test fixture đã kiểm chứng prior-process operation chuyển thành orphaned, không nhận lại Python worker cũ.

### 4.2. Upstream thực sự có gì, và vì sao không port nguyên khối?

Đã xác định upstream từ `README.md:472`: `yyjeqhc/webcodex`. Nhánh khảo sát kiểm tra GitHub API và `git ls-remote`, pin commit **`19a83aaa440f8c5ecbb53709fee5dbab6b81fdc1`**, subject `Prefer guarded text edits and preserve ChatGPT session identity (#328)`. Task chính đọc lại các source quyết định tại commit này; không fetch/merge upstream vào checkout.

| Bằng chứng upstream tại commit đã pin | Điều xác minh được | Ý nghĩa áp dụng |
|---|---|---|
| [AgentTask storage](https://github.com/yyjeqhc/webcodex/blob/19a83aaa440f8c5ecbb53709fee5dbab6b81fdc1/crates/webcodex-store/src/agent_task.rs#L498) | Có `wc_agent_tasks`, `wc_agent_task_attempts`, `wc_agent_task_coding_runs`, index một active attempt, lease/fence/generation | Học exact ownership và replay invariants; không nhân đôi ledger/lease của Python |
| [Wake storage](https://github.com/yyjeqhc/webcodex/blob/19a83aaa440f8c5ecbb53709fee5dbab6b81fdc1/crates/webcodex-store/src/agent_wake.rs#L242) | Wake và delivery attempt riêng, coalescing indexes, trạng thái `delivery_unknown` | Giữ dispatch uncertainty; không blind retry sau mất phản hồi |
| [Wake controller](https://github.com/yyjeqhc/webcodex/blob/19a83aaa440f8c5ecbb53709fee5dbab6b81fdc1/src/agent_wake.rs#L115) | Queue bounded/deduplicated và process-local worker, `schedule_agent` | Có event-driven wake substrate; không tự suy ra general AgentTask scheduler hoặc ChatGPT host support |
| [AgentTask tool definitions](https://github.com/yyjeqhc/webcodex/blob/19a83aaa440f8c5ecbb53709fee5dbab6b81fdc1/crates/webcodex-tool-contracts/src/tool_definition/agent_tasks.rs#L22) | Chín tool definitions dành cho AgentTask/Attempt | Không nhập trực tiếp vào tám public `smart-v3` tools |

Architecture upstream phân biệt rõ A3 start attempt là ownership/fencing, không tự tạo Job/Workflow Session/Wake/callback. Nó cũng nói chưa có production ChatGPT auto-resume adapter được chứng minh trong repository/supported protocols; fake adapters chỉ kiểm tra dispatch semantics. Đây là giới hạn của triển khai đó, không phải phủ định mọi sản phẩm OpenAI. [Upstream durable-runtime boundary](https://github.com/yyjeqhc/webcodex/blob/19a83aaa440f8c5ecbb53709fee5dbab6b81fdc1/docs/architecture/durable-agent-runtime.md).

Local Cargo workspace có các crate hiện hữu nhưng không có cùng `webcodex-store`/`webcodex-tool-contracts` layout; product đang vận hành còn là Python/Electron. Ngoài ra Rust foundation local đã có Connector Task riêng (`src/db/task_kernel.rs:1`). Vì vậy có nguy cơ chồng ba lớp task nếu nhập schema/dispatcher theo tên. Không nên mở việc chuyển authority sang Rust chỉ để giải một gap continuation.

**Mức bằng chứng upstream:** source đã đọc và checked-in test coverage đã khảo sát, không build/test upstream trong lượt này; chưa có runtime, package hay host proof tại dự án của người dùng. Lấy invariants/test ideas rồi map vào existing identity là phương án nhỏ hơn và phù hợp current roadmap hơn.

## 5. Bằng chứng runtime đọc tại thời điểm nghiên cứu

### 5.1. Canonical lifecycle snapshot

Quan sát bắt đầu `2026-09-07T11:07:27.779771Z`; snapshot hoàn tất `2026-09-07T11:07:29.390Z` (18:07 giờ Việt Nam).

- Backup API copy, immutable/query-only; `canonical_writer_instantiated=false`, `runtime_instantiated=false`, `mutated_canonical_ledger=false`.
- Schema `12`; SQLite integrity `ok`; foreign-key check `0` rows.
- Snapshot SHA-256: `f7f338213173376a9736978334b87457d3c22b70815c8a6713e11a9752c2a9d4`.
- Logical SHA-256: `aae5ac1d844a8e1944dae80143acf9464728bb6863a0d8cd09c9d26ee8f98162`.

| Dữ kiện trong snapshot | Giá trị | Giới hạn diễn giải |
|---|---:|---|
| RUN / WAVE / checkpoint | 289 / 413 / 118 | Inventory hiện lưu trong canonical DB; không phải toàn bộ lifetime đã archive |
| Problem Revision / knowledge checkpoint | 1 / 1 | Không phải cohort đủ lớn để kết luận hiệu quả |
| Handoff capsules | 2 | Presence không chứng minh journey hoàn thành |
| Managed process rows, mọi lifecycle | 5.018 | Là lịch sử; không phải 5.018 process đang chạy |
| Active managed jobs theo census | 0 | Chỉ managed inventory được census quan sát; không phải chứng minh toàn bộ máy không có process |
| Ordinary active RUNs | 49 | 45 stale candidates theo threshold, 3 inactive trong grace, 1 awaiting acceptance |
| Unexplained active / unbound live residue | 0 / 0 | Không cấp quyền reconcile hoặc terminate |
| Projection drift | `true` | Không dùng task-state projection làm causal truth |

Sáu P5 experiment anchors được giữ riêng. Không auto-resume 49 RUN chỉ vì `status=active`; đặc biệt không tái khởi động stale records hoặc vượt acceptance barrier. Nghiên cứu này không reconcile, release lease, dọn evidence hay thay đổi runtime.

### 5.2. Chạy oracle continuity trên dữ liệu hiện hữu

Một Backup API snapshot riêng được đọc lúc `2026-09-07T11:09:08.258008Z`. Dùng `ProblemLineageFacts`, `CrossSessionContinuityFacts` và `cross_session_continuity_report`; không tạo Problem, session hay receipt thử nghiệm trong ledger thật.

- Có đúng **1 Problem Revision** trong tập được đọc; fact window không truncated.
- Có **1 knowledge checkpoint, 6 ACK và 6 reattach receipts** tổng thể.
- Kết quả exact journey: **`INCOMPLETE`**; `accepted_real_cross_session_continuity_receipt=false`.
- **7 PASS, 3 INCOMPLETE, 9 UNAVAILABLE**, tổng 19 gate.

Các missing gates quyết định gồm product Session A/B thực, NO_ADVANCE observation, UI observation, exact continuity-core recording, intentional rotation, exact same-role reattach của journey, same-Job reobservation không duplicate, session B reconstruction, hoàn tất criterion còn lại, closure/falsifier và independent outcome/reopen.

**Sáu reattach receipts tổng thể không làm TG6-13 tự PASS:** oracle vẫn thiếu receipt khớp đúng journey/role/revision. Đây là lý do cần đo exact end-to-end, không dùng số lượng bảng hoặc giao diện “ACTIVE” thay thế.

### 5.3. Projections bổ trợ và độ tươi

Đọc lúc `2026-09-07T11:10:16.8605788Z`:

- `performance.json`: SHA-256 `56360f1886d8a357a0b2ed86db23747878a3bc2ba73097ff70fff7e198f0cd72`; 44.253 tool calls, 3.183 errors; `last_finished_at=2026-09-07T04:26:53.337Z`.
- `task-state.json`: `status=stopped`, `updated_at=2026-09-07T03:17:18.338Z`.
- `task-history.json`: 100 archived projection entries; file last-write được quan sát là `2026-08-25T01:35:45Z`.

Các projection không cùng observation window với causal ledger và không dùng để tính “tỷ lệ lỗi do đứt turn”. Counters không phải provider billing; thiếu chi phí/model usage/natural outcome vẫn là unknown. Không thể kết luận ROI hoặc thứ hạng ưu tiên chỉ từ những số này.

## 6. Đường continuation chính thức và giới hạn thực tế

### 6.1. MCP Tasks và Sampling không tự cấp quyền cho ordinary chat

MCP Tasks trong đặc tả `2025-11-25` là experimental, phục vụ durable request state và deferred result retrieval, có capability negotiation. Polling `tasks/get` đúng giao thức không phải “hack”; nhưng poll trạng thái không đồng nghĩa khởi động một ChatGPT reasoning turn. [MCP Tasks](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/tasks).

MCP Sampling có `sampling/createMessage`, nhưng client phải công bố capability và vẫn kiểm soát model/permission. Do đó phát biểu “MCP không bao giờ yêu cầu inference được” cũng quá rộng; phát biểu đúng là dự án chưa chứng minh client ChatGPT đang dùng hỗ trợ và cho phép flow này trong lifetime cần thiết. [MCP Sampling](https://modelcontextprotocol.io/specification/2025-11-25/client/sampling).

### 6.2. UI follow-up: đáng thử, không phải background host

OpenAI mô tả `window.openai.sendFollowUpMessage` để component yêu cầu ChatGPT đăng thông điệp. Reference cũng ưu tiên MCP Apps bridge khi có tương đương chuẩn. Đây là extension của host, không phải server tự sửa composer. [OpenAI UI reference](https://developers.openai.com/plugins/reference).

Suy luận áp dụng cho dự án: có thể nghiên cứu một adapter nhỏ khi UI đang mount, với capability detection, wake ID và quyền người dùng rõ. Chưa có bằng chứng về hoạt động khi tab background/throttled, widget unmount, browser đóng hoặc host bận. Không dùng vòng tự gửi prompt, DOM automation hoặc undocumented HTTP làm bảo đảm continuity.

### 6.3. Workspace Agents API: một lựa chọn mới cần thêm vào quyết định

Tài liệu chính thức mô tả trigger từ server vào **published Workspace Agent**, dùng `conversation_key` để giữ conversation và `Idempotency-Key` khi retry cùng event. API có response accepted và beta run-status; nội dung trả lời của agent chưa lấy được qua API theo trang này. [Workspace Agents trigger API](https://learn.chatgpt.com/workspace-agents/trigger-runs).

Đây không phải endpoint resume tùy ý conversation ordinary chat. Khả năng áp dụng còn phụ thuộc quyền Workspace Agent, published channel, token được cấp đúng, MCP connection, approval policy và bằng chứng callback về ledger. Workspace Agent controls khác Work access và local Codex configuration. [Work admin FAQ](https://learn.chatgpt.com/docs/enterprise/work-admin-faq).

**Chưa thử trên account của người dùng; không đã-publish, không trigger API và không tự tạo access token.** Trong spike tương lai, trạng thái `completed` từ host cũng chỉ là host run terminal, không phải acceptance/outcome của Problem trong Codex-web.

### 6.4. Host sở hữu inference loop

Official docs chỉ dẫn Work cho hosted long-running work. App Server cung cấp thread resume và turn start; local `codex_bridge.py` đã dùng primitives tương ứng. Đây là đường có cơ sở để bỏ phụ thuộc vào một ordinary chat turn, nhưng thay đổi vai trò controller/worker là quyết định sản phẩm và authority, không phải bước port dữ liệu thuần túy. [Long-running work](https://learn.chatgpt.com/docs/long-running-work), [Codex App Server](https://learn.chatgpt.com/docs/app-server).

Responses API background mode là một lựa chọn khác cho request inference dài; app vẫn phải xử lý state/tool loop và budget của mình. Nó không biến thành quyền dùng ChatGPT conversation/subscription hiện có. Không mở nhánh API riêng nếu host/bridge hiện có đã giải được use case. [OpenAI background mode](https://developers.openai.com/api/docs/guides/background).

### 6.5. Bài học từ dự án khác

Cline xác nhận task có ID, storage, history và khả năng resume qua session. OpenHands có persisted conversation state/events, kiểm tra ID khi restore, iteration bound và stuck detection. Chúng chứng minh mẫu thiết kế đáng học, không chứng minh ChatGPT connector của Codex-web tự wake được. [Cline task management](https://github.com/cline/cline/blob/main/docs/core-workflows/task-management.mdx), [OpenHands ConversationState](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/conversation/state.py).

OpenHands issue #14260 ghi nhận ACP session state nằm trong sandbox bị recycle, khiến resume hỏng. Issue hiện hiển thị **Closed**; chỉ dùng như failure mode lịch sử, không trình bày là bug đang tồn tại ở mọi version hiện tại. [OpenHands #14260](https://github.com/OpenHands/OpenHands/issues/14260).

## 7. Phương án tối thiểu cho Codex-web

Đây là khuyến nghị, không phải những thay đổi đã được triển khai.

### KEEP

- Problem Revision, contract capsule và outcome semantics hiện có.
- RUN/WAVE, canonical ledger, exact proof/checkpoint, controller lease và write fence.
- Continuity Core, ACK/reattach guards, handoff capsule và reporter làm oracle độc lập.
- Process ownership/kill-tree protections và public `smart-v3` đúng tám tools.

### MODIFY chỉ khi ca thực chứng minh khoảng trống

1. **Tái sử dụng continuation checkpoint:** exact Problem/workspace, knowledge revision, current RUN/WAVE, Job IDs/cursors, pending criterion/action và reference tới proof. Không persist raw transcript để giả durable context.
2. **Thêm pending continuation intent tối thiểu nếu chưa có representation phù hợp:** trước hết đánh giá `coordination_messages` + `handoff_capsules` hiện có; cần event/reason + exact scope + dedupe identity + delivery state + budget/pause. Generic message ACK chưa có đầy đủ wake/source/generation semantics; không dùng ACK đó để cấp quyền. Dùng cùng ledger/authority; không sao chép toàn bộ Goal/Task/Attempt database của upstream.
3. **Reattach trước, dispatch sau:** khi host hợp lệ quay lại, validate currentness/role/revision, dùng reattach hiện có, quan sát Job cũ, rồi mới xác định bước tiếp theo. Nhiều task/endpoint không được resolve bằng recency hay cwd fallback.
4. **Chọn đúng một adapter đầu tiên:** UI follow-up nếu mục tiêu chỉ cần giảm thao tác lúc browser còn mở; host-owned Codex/Work hoặc Workspace Agent trigger nếu yêu cầu browser đóng vẫn chạy. Không triển khai mọi adapter cùng lúc.
5. **Observation phải đủ bền:** giữ log cursor/output/exit evidence cần để đọc lại. Job row còn nhưng output mất phải báo thiếu, không biến thành test pass.

### KHÔNG thêm ở vòng đầu

- Durable Agent/Conversation/Inbox abstraction đa tenant, đa project hoặc đa protocol khi chưa có use case thứ hai.
- TaskAttempt state machine có quyền riêng, chạy song song với RUN/WAVE.
- Scheduler tự nhận tất cả `active` RUN, tự đổi route, lấy lease hoặc tự ACCEPT.
- Global automatic routing, billing estimator mới, transcript memory engine, hay framework mới không giải quyết failure mode đã đo.

### Invariants của candidate

- Turn/transport kết thúc **không tự terminalize Problem**; cũng không mở quyền chạy vô hạn.
- User cancel/abandon là terminal có chủ đích; pause, hết budget, cần input/authority phải được biểu diễn thật và có cách resume hợp lệ.
- State thực thi và trạng thái vấn đề là hai chiều riêng; không ghi đè PRL bằng enum trong tư vấn.
- Dispatch chỉ dưới đúng controller lease/fencing generation; foreign active lease và stale source/runtime phải fail closed.
- Retry delivery cùng event không tạo hai tác dụng được cấp quyền. Không hứa exactly-once với shell side effects không idempotent; unknown execution phải reobserve/reconcile trước retry.
- Wake không phải proof, không phải write authority, không phải final acceptance.
- Technical acceptance chỉ là mức chứng minh của attempt; full-problem outcome vẫn cần receipt độc lập hoặc truthful same-revision reopen.

## 8. Kế hoạch kiểm chứng trước khi mở implementation lớn

| Giai đoạn | Việc cần làm khi được duyệt | Gate để đi tiếp |
|---|---|---|
| F0 — Chọn host và acceptance boundary | Chốt có cần browser đóng vẫn chạy hay chỉ reattach khi host quay lại; kiểm tra capability/account/permissions | Có một trigger flow chính thức và một consumer có quyền; nếu không, không hứa autonomous ordinary chat |
| F1 — Quan sát baseline thật | Một natural Problem hiện có, giữ scope và source identity; dùng oracle TG6, không manufacture receipt | Phân loại exact missing step; chỉ sửa defect được quan sát |
| F2 — Thin continuation slice | Một checkpoint/intent path và một adapter, reuse RUN/WAVE/reattach/Job | Idempotent delivery, stale/foreign rejection, pause/budget, no duplicate effect đều có focused proof |
| F3 — Failure-boundary pilot | Browser disconnect, host busy, MCP restart và executor loss là case riêng; restart chỉ qua supported flow được cho phép | Trạng thái và Job/output identity đúng; interrupted/unknown không được giả recovered |
| F4 — Natural end-to-end | Tiếp tục cùng Problem, giải quyết criterion còn lại, technical acceptance rồi independent outcome/reopen | TG6 exact receipt phù hợp; tách no-user-reprompt metric khỏi merely reattached |
| F5 — Quyết định mở rộng | 5–10 natural Problems theo roadmap; ghi coverage, TTAR/TTPR, số lần “tiếp tục”, duplicate/rework và chi phí nếu thật sự đo được | Có giá trị quan sát được dưới safety floors; mẫu nhỏ không đủ tự promote policy/routing |

Ca “sửa bug HR” trong tư vấn chỉ là ví dụ. Không được mở workload ở `E:\DEV\HR STA\HR` hoặc dùng dữ liệu HR nếu người dùng chưa đặt workspace/case đó trong scope.

### Bộ kiểm tra chấp nhận tối thiểu cho spike

1. Cùng owner còn sống: ngắt browser khi Job đang chạy, quay lại đọc đúng `job_id` và cursor; marker side effect xuất hiện một lần.
2. Model turn kết thúc sau dispatch: Goal chưa terminal, pending action được giữ, không tự `ACCEPTED`.
3. Crash sau khi nhận dispatch nhưng trước khi trả receipt: reobserve theo identity/dedupe, không blind retry.
4. Hai wake trùng hoặc hai endpoint tranh quyền: một ownership transition hợp lệ; stale generation bị từ chối.
5. Source, runtime behavior hoặc Problem Revision đổi: checkpoint cũ không được dùng để mutation/proof acceptance.
6. Host không hỗ trợ trigger hoặc account chưa có quyền: báo capability/authority blocked, không self-prompt/DOM workaround.
7. MCP restart trong Windows containment path: chứng minh behavior thực tế; child chết/handle mất thì báo đúng, không “reattach PID”.
8. Owner/executor restart hoặc máy reboot: giữ goal/evidence; không gọi đây là cùng process sống sót.
9. User pause/cancel, budget hết, no-progress lặp: scheduler dừng đúng ý định và không đánh thức tiếp trái lệnh.
10. Test pass nhưng acceptance hoặc outcome chưa có: dừng ở đúng barrier; không biến host-completed thành Problem-resolved.

Chỉ case có **host tự tạo continuation được quan sát mà không có user reprompt** mới chứng minh “không phải nói tiếp tục”. Mở browser rồi người dùng gửi một prompt/bootstrap không được tính là autonomous wake; nó chỉ chứng minh recovery-on-next-contact.

## 9. Chi phí, rủi ro và điểm quyết định

Không đủ bằng chứng để ước lượng phần trăm hoàn thành, số ngày port hay ROI. Độ khó không chủ yếu nằm ở thêm bảng; nằm ở ownership, replay, process lifetime, host capability và acceptance semantics.

- **Rủi ro cao nhất:** port xong task/wake nhưng không có host consumer, trải nghiệm vẫn phải gõ “tiếp tục”. F0 phải đi trước.
- **Rủi ro thứ hai:** nhập runtime Rust vào operated Python/Electron rồi có hai authority/DB/lease. Ưu tiên học invariant và test, không nhập toàn hệ thống.
- **Rủi ro thứ ba:** restart/sự cố mất output khiến scheduler suy rằng chưa chạy và tạo side effect trùng. Phải có dispatch uncertainty handling.
- **Rủi ro vận hành hiện hữu:** projection drift và stale inventory làm heuristic “resume active” nguy hiểm. Nghiên cứu không tự dọn những record này.
- **Rủi ro chi phí:** một inference loop tự động phải có budget và no-progress stop. Cumulative performance counters không cung cấp provider billing hoặc effective task ROI.
- **Rủi ro mở rộng scope:** đưa Codex lane hoặc published Workspace Agent thành controller là thay đổi trách nhiệm được cấp quyền; không thực hiện ngầm dưới tên continuation.

**Ưu tiên đề xuất:** chứng minh một natural journey và host trigger có thật; sau đó bổ sung cầu nối nhỏ nhất. Không đảo toàn bộ roadmap chỉ từ kết luận tư vấn.

## 10. Validation đã thực hiện

Tại `E:\DEV\Codex-web\resources\coding-tools-mcp`:

```powershell
python -m pytest -q -p no:cacheprovider tests/test_controller_continuity.py tests/test_cross_session_continuity_report.py -k 'policy_checkpoint_idempotency_conflict_and_reopen_durability or ack_statuses_are_typed_idempotent_and_never_advance or cross_instance_exact_replay_advances_once or source_and_runtime_currentness_fail_closed or task_control_schema_is_strict_and_public_tool_count_is_unchanged or durable_reattach_receipt_survives_later_transport_session_rotation or no_duplicate_execution_claim_requires_reobservation_receipt or closure_and_independent_outcome_are_separate_required_receipts'
```

Kết quả: **8 passed, 19 deselected, 1.94s**.

```powershell
python -m pytest -q -p no:cacheprovider tests/test_codex_bridge.py -k 'persistent_lane_can_be_resumed_by_a_new_bridge_instance or persistent_resume_rejects_workspace_or_session_mismatch'
```

Kết quả: **2 passed, 16 deselected, 0.08s**. Đây là mocked App Server contract, không có provider call và không phải real process restart proof.

```powershell
python -m pytest -q -p no:cacheprovider tests/test_controller_reattach.py tests/test_durable_coordination_runtime.py -k 'active_run_transfers_atomically_and_old_endpoint_stays_fenced or runtime_orphans_only_operations_from_a_prior_process'
```

Kết quả: **2 passed, 16 deselected, 1.63s**. Hai fixture kiểm tra atomic lease transfer/stale endpoint fencing và prior-process background operation trở thành orphaned. Không restart service thật. Tổng cộng **12 tests PASS**, không lặp lại test đã có kết quả.

Reporter/query sources để tái lập read-only observation: `ledger_analysis.py:98`, `lifecycle_census.py:136`, `scripts/report_lifecycle_census.py`, `scripts/report_cross_session_continuity.py`. Census đọc aggregate/classification; continuity reporter chọn exact Problem Revision có thật. Không dùng constructor canonical writer hoặc tự ghi receipt để tái lập kết quả.

Source hashes ghi sau focused proof:

| File trong package | SHA-256 |
|---|---|
| `coding_tools_mcp/controller_continuity.py` | `99b7b01f16036b3195ff555d849335973af2a2add03a43c5b3208ae6fe323a3d` |
| `coding_tools_mcp/cross_session_continuity_report.py` | `edbcc26ea0182c09c50cbb80709bc7b1f9d66cec115c9518740f1159e2cc86da` |
| `coding_tools_mcp/coordination.py` — existing WIP | `aae7c6221518c0149e46e569bbf865acf8f86709f958291760fb0128750727dd` |
| `tests/test_controller_continuity.py` | `0cd6a0d2d2eaefd64e2e3cb71b9e4ea0a21ef94ea9b0acdfacfd7109d547518e` |
| `tests/test_cross_session_continuity_report.py` | `299cec5ccf7725520f5d54247cff73aa054a516194a7ea4b07ca2d1e403522d6` |

Đây không phải fingerprint của toàn runtime hoặc proof-reuse receipt. Không chạy Cargo/full npm/full Python suite vì không thay source và focused checks đã đủ cho các claim được kiểm tra. Không test upstream, account feature, live adapter, browser/UAT, packaged build hay production/SLO trong lượt nghiên cứu.

Document QA: `git diff --check` không có lỗi whitespace; vì report là file mới chưa tracked, kiểm tra riêng nội dung report cho kết quả 0 trailing-whitespace lines, 0 conflict markers, code fences cân bằng, các hash đúng độ dài, upstream links cùng commit pin và 0 findings từ `findSensitiveContentIssues` của repository. Đây là guard nội dung có scope hẹp, không phải xác nhận security toàn repository.

## 11. Trạng thái bàn giao nghiên cứu

- Hoàn tất phần đối chiếu source/contract, upstream commit-pinned, hai live-data read-only snapshots, projection freshness và 12 focused tests.
- Tài liệu được tạo: `docs/research/260907_DURABLE_CONTINUATION_FEASIBILITY_ASSESSMENT.md`; không sửa sản phẩm hoặc runtime evidence.
- Candidate implementation, host/account capability và real automatic continuation chưa được chứng minh; đây là gate cho bước sau, không phải một implementation đã thất bại.
- Không commit/push/release/deploy/service operation. Existing source WIP và `.coding-tools/**` giữ nguyên; không stage delivery vì không có yêu cầu commit/push.
- Postflight HEAD vẫn là `58dfd3093d7a05f6999fe93e15c94050aa51d204`. Trong thời gian nghiên cứu xuất hiện thêm concurrent WIP ở `electron/services/runtimeOrchestrator.js`, `package.json`, `completion_readiness.py` và các release/lifecycle/task-state tests. Không nhận các thay đổi này là sản phẩm của nghiên cứu và không chỉnh/revert chúng. Focused test results là receipt tại thời điểm chạy, không phải chấp nhận toàn bộ checkout đang tiếp tục thay đổi.
- Bước tiếp theo chính xác nếu chấp thuận hướng này: **F0 — chọn một host execution surface và kiểm chứng quyền trigger/reattach của surface đó trước khi viết scheduler hoặc port schema**. Nghiên cứu này không tự chuyển sang implementation hay tạo automation.
