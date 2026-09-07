# Kế hoạch theo đuổi mục tiêu hiệu quả Codex-web — bản triển khai

> Ngày lập: 07/09/2026, Asia/Saigon. Baseline khảo sát bổ sung: 12:15–12:18.
> Repository: `E:/DEV/Codex-web`; nhánh `main`; HEAD `24186fefbdbb9c1dca450ae5e96df167be93c87e`.
> Trạng thái tài liệu: kế hoạch được cụ thể hóa để bàn giao triển khai; không phải báo cáo W0–W8 đã thực hiện.
> Phần A–F là hướng dẫn điều hành cập nhật. Phụ lục bảo toàn nội dung yêu cầu được đính kèm, bao gồm các snapshot cũ; không dùng snapshot đó làm authority hiện tại.

## A. Mục tiêu, phạm vi và điều kiện hoàn thành

Yêu cầu hiện tại là lập kế hoạch theo đuổi toàn bộ mục tiêu trong tệp đính kèm. Deliverable của lượt này là tài liệu có thể thực thi và kiểm tra, không phải tự động triển khai sản phẩm. Hoàn tất tài liệu không đóng mục tiêu hiệu quả sản phẩm, W0–W8 hoặc G0–G10.

Giữ nguyên cả ba mức: kỹ thuật/vận hành; hiệu quả trên HR/PFM và Codex-web; sẵn sàng phát hành. Hai ngưỡng hiệu quả phải đồng thời đạt: p90 thời gian chủ động treatment/control ≤ 0,80 và thao tác làm lại không cần thiết trên mỗi Problem treatment/control ≤ 0,70. Không hạ quality floor, authority, privacy, provenance hoặc independent outcome. Accounting/máy mới thiếu thì gate tương ứng vẫn mở; không biến thiếu dữ liệu thành zero hoặc DONE.

Nguồn yêu cầu: `C:/Users/Admin/.codex/attachments/afd10e82-2e1d-42d4-853f-e2fb7ca21b89/pasted-text-1.txt`; SHA-256 `FE1F46F6FC00206300C51DAE58E118B7AFDCDBE6AFDA9BBDCB8170FD9243296D`.
JSON lịch sử: [codex_web_history_evidence_2026-09-07.json](codex_web_history_evidence_2026-09-07.json); SHA-256 `D3E9D5DEE963C9F0E4CF91B0C1F903949C9A531702D7135CEED629C2D29E3EE3`.

## B. Delta hiện tại: điều gì đã thay đổi so với bản đính kèm?

| Kiểm tra mới | Kết quả quan sát | Hệ quả hành động |
|---|---|---|
| Git | HEAD hiện tại 24186fe, không còn là cd53817 trong snapshot cũ; lúc bắt đầu chỉ ledger.sqlite3 có thay đổi chưa commit. | Không reset/rebase để quay lại expectation cũ; recapture exact identity trước mỗi implementation packet. |
| Lịch sử ledger | Helper chỉ đọc liệt kê ledger hoạt động: 273 RUN, 9.113 event; một archive: 1.118 RUN, 34.000 event. | Đây là inventory theo shard, không phải tổng distinct được kiểm toán; không dùng active ledger đơn lẻ thay population lịch sử. |
| Proof/context/bridge/semantic | So sánh bốn module với cd53817 không có diff. Source còn trả proof nguồn trên cache hit, hash summary theo ID, native giới hạn 8 query và wake predicate chỉ xét server_request/terminal. | Tái sử dụng kết quả khảo sát đúng file; regression của bản sửa vẫn phải chạy trên identity mới. |
| Runtime, census, cohort và billing | Không recapture runtime/census/economics trong lượt tạo tài liệu này. | Các con số 637/93, 36 stale candidate, trạng thái connector và proof test trong phụ lục là snapshot trước; chưa xác nhận lại hiện trạng. |
| Quyền thực thi | Không có Coding Tools MCP task_control/document_workflow khả dụng trong tool catalog của lượt này. | Không giả lập accept/ACK hay dùng shell để thay authority. Tài liệu local không phải EOCL acceptance. |

Kiểm tra lịch sử mới dùng `python -B scripts/query-ledger-history.py --workspace E:/DEV/Codex-web list`. Helper mở mode=ro; kết quả không chứng minh archive integrity, causal joins, absence of duplicate rows hay atomic cross-shard snapshot. Không chạy archive, sửa SQLite hoặc thay manifest trong lượt này.

### B1. Bổ sung bắt buộc vào W0 và W4: bảo toàn mẫu sau archive

Trước tính lại economics, kiểm tra manifest, SHA/hash khi manifest cung cấp, integrity/FK của bản sao và schema từng shard; resolve các RUN được tham chiếu trong kế hoạch tới đúng shard. Active ledger dùng Backup API/query-only; archive phải có hash ổn định trước/sau đọc. Nếu inventory hoặc hash thay đổi giữa cửa sổ, bỏ kết luận cross-shard đó và recapture, không gộp hai snapshot không nhất quán.

Đối soát khóa RUN/WAVE/proof/event, duplicate và foreign joins trước tổng hợp. Không cộng trực tiếp bộ đếm shard để tuyên bố distinct population. Historical chain/receipt vẫn giữ origin; không nối hoặc viết lại hash chain. Nếu reporter hiện có chỉ đọc active ledger, ghi rõ population bị giới hạn và chỉ mở rộng read-only fact loading đủ phục vụ cohort đã chốt; không xây warehouse, không migrate/archive thêm chỉ để làm báo cáo.

Cohort tự nhiên mới tiếp tục được phân biệt với lịch sử. Không tự nhận tệp archive đã có là bằng chứng bảo toàn hoàn chỉnh khi chưa kiểm tra.

## C. Bảng công việc để người triển khai nhận ngay

Trạng thái dưới đây là trạng thái lập kế hoạch, không phải trạng thái EOCL. Một chủ sở hữu tích hợp giữ interface và final acceptance; chỉ có một writer trên mỗi file. Không tự khởi tạo thêm agent/RUN/automation từ tài liệu này.

| Packet | Phụ thuộc | Phạm vi sở hữu dự kiến | Bằng chứng đầu ra | Điều kiện dừng và bước tiếp |
|---|---|---|---|---|
| W0 baseline | Không | Tài liệu này, receipt hiện có; đọc runtime/ledger/archive | Exact source + scope + snapshot + gate register | Thiếu supported authority: ghi blocker; vẫn làm phần source-only được phép. Không tuyên bố live-ready. |
| W1 proof/acceptance | Identity W0 | proof_ledger, context_tools, acceptance_receipts, focused tests liên quan | Cross-wave reuse receipt idempotent; fingerprint canonical; integration acceptance regression | FP/scope sai hoặc duplicate receipt: sửa trước acceptance; không nới cache. |
| W2 completion readiness | W1 | workflow/context/build verification; output/schema docs nếu thay | Typed readiness và missing-step recovery; oracle đúng cấp criterion | Không rõ command effect/authority: không tự chạy hoặc cài dependency. |
| W3a observation | Source baseline ổn định | codex_bridge + tests | Meaningful wake, bounded wait, cursor gap, independent consumer | Wrong identity/mất lịch sử: refresh rõ ràng, không restart job. |
| W3b semantic | W0; không overlap W2 writer | semantic_localization/context + tests | 8+4 tuần tự, deadline tổng, per-query fallback, release lease | Provider/authority unavailable: fallback; không sửa binding ngoài quyền. |
| W4 economics | W0 archive population; W1 lineage | Reporter/usage/journey hiện có + tests | Problem-level all-attempt economics; segment/clock/coverage receipts | Không exact attribution: unknown; không ép khớp totals. |
| W5 natural journey | W1–W4 + runtime hợp lệ | Yêu cầu HR/PFM thật được giao riêng | Revision→attempt→proof→checkpoint→outcome/reopen qua phiên | Thiếu yêu cầu nghiệp vụ/quyền/oracle: cần input đó; không tạo synthetic filler. |
| W6 cohort | W5 | Natural cohort/reporter + bounded advisory nếu có bằng chứng | Checkpoint 5/10 liên tiếp; continuity riêng; ranking tổn thất | Thiếu volume: giữ collecting; không bỏ mẫu khó hay thất bại. |
| W7 experiment | W6 + common baseline + quyền mở | P5 manifest/store/analyzer hiện có | Versioned Problem assignment, multi-attempt lineage, A/A rồi A/B | Source/arm/clock/receipt drift: pause/hard-stop bằng surface hỗ trợ. |
| W8 release | Baseline kỹ thuật; không cần chờ W7 để chuẩn bị | Entry point release/CI/runbook hiện có | Exact-source Node+MCP+artifact+packaged/installed/máy mới receipts | Thiếu máy mới/publish authority: nhánh đó mở; không giữ kỹ thuật hostage. |
| G10 disposition | W6/W7 cho efficacy; W8 cho release | Tài liệu này và phạm vi redundant đã chứng minh | KEEP/MODIFY/REMOVE kèm căn cứ | Không đạt hai mục tiêu thì efficacy chưa đóng, dù đã bỏ micro-policy. |

W1 và W2 tuần tự vì chung proof/completion contract. W3a có thể độc lập; W3b không chạy writer đồng thời trên context_tools với W2. W4 phải đủ trước lấy dữ liệu mới làm chứng cứ efficacy. Nhánh chuẩn bị W8 chạy độc lập, nhưng không mượn proof của artifact/source khác.

### C1. Điểm vào mã và kiểm thử đã xác định

Các đường dẫn dưới đây tính từ `E:/DEV/Codex-web/resources/coding-tools-mcp`.

| Packet | Điểm vào mã | Test hiện có cần mở rộng |
|---|---|---|
| W1 | coding_tools_mcp/proof_ledger.py; context_tools.py; acceptance_receipts.py; coordination.py | tests/test_proof_ledger.py; test_acceptance_file_attestation.py; test_orchestration_workflow.py |
| W2 | coding_tools_mcp/workflow_tools.py; context_tools.py; build_verify.py; agent_candidate.py | tests/test_task_state_and_build.py; test_pytest_selector_paths.py; test_orchestration_workflow.py |
| W3 | coding_tools_mcp/codex_bridge.py; semantic_localization.py; context_tools.py | tests/test_codex_bridge.py; test_semantic_localization.py; test_task_state_and_build.py |
| W4 | coding_tools_mcp/accepted_result_economics_report.py; problem_resolution_economics.py; problem_resolution_journey.py; usage_events.py; performance_trace.py | tests/test_accepted_result_economics_report.py; test_problem_resolution_economics.py; usage/trace tests sở hữu behavior thay đổi |
| W5–W7 | coding_tools_mcp/cross_session_continuity_report.py; natural_problem_cohort.py; p5_experiment.py; p5_experiment_store.py; egri_p5_continuity_readiness.py | tests/test_cross_session_continuity_report.py; test_natural_problem_cohort.py; test_p5_experiment.py; test_p5_measurement.py; test_p5_treatment.py; test_egri_p5_continuity_readiness.py |

Lệnh khởi đầu W1 sau khi được giao implementation: `python -B -m pytest tests/test_proof_ledger.py tests/test_acceptance_file_attestation.py tests/test_orchestration_workflow.py -q -p no:cacheprovider` từ package root. Viết regression tái hiện gap trước bản sửa, rồi giữ test đó sau sửa. Các gói khác chọn test trong owner tương ứng, không chạy toàn repository theo nghi thức. Đụng module extraction thì làm đúng package AGENTS; kiểm tra module-size khi thêm code.

Các lệnh release dự kiến vẫn là `npm test`, `npm run test:mcp`, đường builder hiện có, packaged smoke và `node scripts/installed-recovery-smoke.js`. Không chạy lệnh cài đặt/runtime/paid canary chỉ vì nó xuất hiện trong kế hoạch.

## D. Hợp đồng thực thi và đo lường không để người triển khai đoán

### D1. Proof, readiness và observation

Cross-wave receipt mới phải có current RUN/WAVE, fingerprint exact, source_proof_id, cache_hit và executed=false; duration execution=0 không phải tuyên bố tổng overhead=0. Same-wave hit giữ ID. Duplicate reuse phải được chống tại điểm ghi phù hợp; không chỉ kiểm tra trước insert ngoài transaction. Failed proof và foreign workspace tuyệt đối không được nhận. Một cache hit không nới write lease hoặc acceptance authority.

Completion readiness là projection trước thực thi, không là giấy phép và không đảm bảo trước mọi byte tương lai. Dùng chung validator với cổng thực thi/nghiệm thu, recheck đúng thời điểm. Preflight phải phân biệt failing product oracle với command/setup failure; không auto-install, không tự chạy collection có side effect khi chưa có authority. Đầu ra chỉ giữ command hash/trạng thái/tham chiếu đã lọc, không credential hay raw transcript.

Observation cursor phải gắn consumer/thread/turn và instance hiện tại; cursor cũ hoặc evicted trả missing-history/refresh, không suy là unchanged. Shared meaningful predicate dùng cho filtering và wake. Semantic 8+4 dùng một tổng deadline: mỗi nhóm chỉ nhận thời gian còn lại; hết thời gian thì unresolved queries fallback theo contract hiện có, không kéo dài gấp đôi.

### D2. Chất lượng và thời gian tới Trusted Resolution

Đơn vị analysis/randomization của chương trình hiệu quả là Problem Revision; các RUN/WAVE/retry là attempt trong mẫu, không là mẫu độc lập. Thời gian chủ động là union interval hợp lệ trong cùng clock domain qua các attempt cần thiết tới outcome và sửa lại trong follow-up. Không dừng đồng hồ ở acceptance kỹ thuật đầu tiên. Post-accept observation cần thiết để xác nhận outcome phải được nhận diện riêng, không tùy ý loại để làm nhanh hơn; quan sát không liên quan về sau được tách riêng.

Ca failed/aborted/timeout/unresolved giữ nguyên ITT denominator. Không trộn các ca chưa giải quyết với một giá trị thời gian nhanh; dùng disposition/censoring theo analysis contract đã khóa. Unknown attribution/cost không bằng zero. Phải báo denominator theo workspace, task class, oracle, model/route, continuity/source baseline và điều kiện semantic; tổng hợp chỉ khi weighting đã đăng ký trước.

Một bounded cohort 5/10 không đủ tính power chắc chắn cho p90. Cỡ mẫu, horizon, follow-up, phương pháp khoảng tin cậy và xử lý censoring là deliverable bắt buộc trước mở W7, được tính từ dữ liệu khả dụng và duyệt trong manifest; chưa có dữ liệu thì không điền số giả. Mục tiêu power 80%, confidence 95% giữ nguyên. Để chứng minh cả mức 20% và 30%, phải đăng ký effect giả định vượt ngưỡng và uncertainty phù hợp; không tính power chỉ cho giả thuyết “khác zero” rồi gọi đạt ngưỡng. Nếu không có cỡ mẫu khả thi, giữ efficacy gate mở và báo feasibility, không sửa threshold sau xem kết quả.

Guard về chất lượng: không critical authority/privacy/data/duplicate-write/false-closure; confirmed outcome, reopen và operator burden không được xấu đi theo tiêu chí đã khóa. Không peeking/optional stopping; an toàn vẫn được quyền hard-stop. Tổng số vòng REPLAN không được dùng thay redundant-rework đã phân loại nguyên nhân.

### D3. Gate quyền và phụ thuộc ngoài

| Việc cần quyền/dữ liệu | Ai cung cấp/quyết định | Hành động khi chưa có |
|---|---|---|
| Implementation/source acceptance qua authority hiện có | Controller được cấp quyền; supported Coding Tools MCP khi dùng EOCL | Đọc/lập packet được; không giả accept hoặc chuyển write owner ngầm. |
| Activation, restart, connector ACK | Operator và Recovery Host đúng installation/epoch | Thu receipt chỉ đọc; yêu cầu đúng hành động thiếu, không raw protocol bypass. |
| Ca HR/PFM và outcome độc lập | Anh/người sở hữu nghiệp vụ, qua surface hỗ trợ | Chờ ca có thật; không tự sửa HR hoặc tạo confirmation. |
| P5 A/A, A/B và paid provider | Operator phê duyệt manifest/cost đúng đích | Không mở epoch hay dispatch trả phí. |
| Host usage transport | Host/client thực sự hỗ trợ receipt có provenance | Giữ G5 thiếu bằng chứng; không scrape hoặc suy ra billing. |
| Máy Windows sạch, login/session, installer lịch sử để upgrade | Operator cấp môi trường/artifact | Giữ release gate tương ứng mở; không giả new-machine/upgrade. |
| Commit/push/tag/publish/deploy | Lệnh riêng chỉ rõ đích | Không thực hiện; khi được phép phải stage/check delivery và bảo toàn evidence. |

## E. Quy tắc theo đuổi và báo cáo tiến độ

Mỗi packet bắt đầu bằng objective, exact scope, base/fingerprint, authority owner, oracle, protected invariants. Kết thúc bằng diff/receipts/test thật, trạng thái source/EOCL/live/package/outcome tách riêng và đúng next action. Không tạo framework quản lý mới; cập nhật bảng trong tài liệu này bằng append-only dated checkpoint khi có kết quả.

Nếu lỗi môi trường: xác định readiness thiếu trước implementation. Nếu fingerprint đổi: vô hiệu phần proof liên quan, không toàn bộ proof không bị ảnh hưởng. Nếu REPLAN: ghi thay đổi evidence/strategy; không retry y nguyên. Nếu thiếu input ngoài: ghi gate+người cung cấp+bằng chứng cần nhận, tiếp tục nhánh độc lập được phép. Không tự bật automation hay cam kết tiếp tục chạy ngầm; scheduling cần yêu cầu riêng.

Bản đính kèm nói ba mức nghiệm thu và đầy đủ G0–G10; không thay thế bằng một số packet đã xong. W0 chỉ hoàn tất khi baseline các claim cần thiết có receipt hoặc được phân loại blocker rõ; việc tạo tài liệu chỉ đóng deliverable kế hoạch. W1–W8 và gate sản phẩm hiện chưa được tài liệu này đánh dấu đạt.

## F. Completion audit của deliverable kế hoạch

| Yêu cầu | Bằng chứng trong tài liệu |
|---|---|
| Đọc và giữ toàn bộ nội dung đính kèm | Provenance/hash ở A; nguyên văn đã chuẩn hóa newline trong phụ lục. |
| Giữ ba mức, cả hai ngưỡng, HR/PFM + Codex-web | A; D2; phần 1 và 4 phụ lục. |
| Đầy đủ W0–W8, interface, tests và G0–G10 | Bảng C/C1/D; toàn bộ phần 2–4 phụ lục. |
| Kế hoạch bám worktree hiện tại, không coi snapshot cũ là current | B và bổ sung archive B1. |
| Có thứ tự, owner, dependency, acceptance và blocker/next action | C, D3, E và nghiệm thu từng WAVE trong phụ lục. |
| Bảo toàn chứng cứ và giới hạn quyền | A, B1, D3, E; không sửa ledger/archive/source trong lượt này. |
| Không đánh đồng kế hoạch và sản phẩm đã đạt | Header, A, E và bảng audit này. |

Kiểm tra bàn giao bắt buộc: tệp tồn tại; phụ lục khớp nội dung nguồn sau chuẩn hóa newline; W0–W8/G0–G10 đủ; các đường dẫn code/test local tồn tại; Markdown không conflict/trailing whitespace; JSON đầu vào không đổi hash; diff chỉ thêm tài liệu bên cạnh ledger dirty có từ đầu. Không cần Cargo/npm/pytest cho thay đổi tài liệu này. Các test nêu trong phụ lục là bằng chứng lượt khảo sát trước, không phải lần chạy mới.

## Phụ lục — Nội dung yêu cầu được bảo toàn

**Lưu ý:** Toàn bộ phần sau là nội dung tệp người dùng đính kèm. Các câu “đã kiểm tra”, HEAD cd53817, số liệu và trạng thái Plan Mode bên dưới thuộc lần khảo sát trước. Chúng không mô tả lượt tạo tài liệu hiện tại. Yêu cầu và tiêu chí vẫn giữ nguyên; delta ở B điều chỉnh điểm bắt đầu triển khai.

<!-- BEGIN ATTACHED PLAN -->
# Kế hoạch hoàn thiện Codex-web: giảm vòng làm lại, giữ đúng bằng chứng và chứng minh hiệu quả trên công việc thật

## 1. Đích đến và baseline đã xác minh

Mục tiêu của chương trình là **giảm thời gian tới một kết quả người dùng thực sự sử dụng được và xác nhận là đúng**, đồng thời giảm công việc làm lại và công sức điều phối. Không lấy số test, số RUN, số tool call hay việc có bản cài làm đại diện cho mục tiêu đó.

Theo lựa chọn của anh, kế hoạch giữ nguyên ba mức nghiệm thu:

| Mức | Điều kiện hoàn thành |
|---|---|
| **Kỹ thuật và vận hành** | Source có provenance, proof và nghiệm thu đúng phiên bản; runtime tải đúng mã; tiếp tục công việc an toàn; không phải xử lý lại những điều kiện hoàn thành đã biết. |
| **Hiệu quả thực tế** | Trên công việc HR/PFM và Codex-web, đạt **cả giảm ít nhất 20% p90 thời gian xử lý chủ động và giảm ít nhất 30% thao tác làm lại không cần thiết**, không làm giảm chất lượng hay tăng gánh nặng người dùng. |
| **Sẵn sàng phát hành** | Có đường kiểm chứng ứng viên phát hành thống nhất, artifact đúng source, kiểm chứng cài đặt/phục hồi và bằng chứng máy mới phù hợp. Publish/deploy vẫn cần lệnh riêng. |

Nếu thiếu accounting của host, dữ liệu tự nhiên hoặc môi trường máy mới, phần có thể làm vẫn tiếp tục; **gate thiếu bằng chứng vẫn để mở, không đổi tên thành hoàn tất**.

### Baseline cho kế hoạch này

Đã đối chiếu hai bản phân tích, [JSON lịch sử anh cung cấp](E:/DEV/Codex-web/docs/research/codex_web_history_evidence_2026-09-07.json), tài liệu hiện hành, source và các truy vấn ledger chỉ đọc tại `main @ cd53817d4bbea97743317e8668ef74dd87fefac3`.

| Phát hiện | Ý nghĩa đối với kế hoạch |
|---|---|
| Ledger được đọc qua bản sao Backup API bất biến; integrity đạt, không lỗi foreign key. | Có thể dùng làm nguồn truy nguyên; không cần xây kho bằng chứng khác. |
| Có 637 RUN accepted thuộc cohort deterministic representative; chỉ 93 RUN còn số liệu tài nguyên, độ phủ khoảng 14,6%. | Các tỷ lệ lịch sử giúp chọn vấn đề cần điều tra, chưa đủ để kết luận hiệu quả toàn sản phẩm. |
| Chưa có chi phí tiền đầy đủ trong cohort; ledger Codex-web đang có một Problem mở, chưa có outcome receipt độc lập. | Chưa chứng minh Trusted Resolution hay hiệu quả kinh tế đầy đủ; không suy rộng sang ledger HR chưa khảo sát. |
| Chưa có accepted cohort khớp HEAD hiện tại đủ để đo lỗi tái diễn. | Không mở lại toàn bộ hardening chỉ vì số lỗi lịch sử cao. |
| Runtime báo source đang chạy khớp trên đĩa, nhưng `fully_ready=false`, `runtime_update_incomplete=true`; chưa có freshness receipt của tiến trình hiện tại. | Chặng đầu cần đóng đúng phần activation/connector còn thiếu, không mặc định restart lại cả hệ thống. |
| Không có managed job hoặc tài nguyên sống thất lạc; 36 dòng active được phân loại là stale candidate nhạy theo ngưỡng. | Không coi đó là 36 job đang chạy; không cưỡng bức dọn để làm dashboard xanh. |
| Đã tái hiện trong ledger tạm: cross-wave proof cache hit không tạo proof receipt ở WAVE mới; fingerprint summary cũng khác fingerprint canonical của acceptance. | Đây là lỗi liên kết bằng chứng cụ thể để sửa trước, không phải đề xuất xây cache mới. |
| Source cho phép 12 truy vấn context nhưng native semantic provider nhận tối đa 8; bridge có khác biệt giữa sự kiện được trả về và sự kiện đánh thức wait. | Có hai gói sửa nhỏ, kiểm thử được, trước khi cân nhắc mở rộng semantic hoặc observation. |

Tài liệu ngày 06/09 đã ghi nhận ứng viên 1.0 được kiểm chứng cục bộ. Kế hoạch **giữ thành quả đó**, chỉ kiểm chứng lại phần thay đổi hoặc phần chưa có bằng chứng ở identity hiện tại.

## 2. Chương trình triển khai theo thứ tự phụ thuộc

Đường găng:

**Baseline chính xác → sửa liên kết proof và điều kiện hoàn thành → đo đúng chi phí → một Problem thật qua phiên → cohort tự nhiên → thí nghiệm → quyết định giữ/sửa/bỏ.**

Nhánh kiểm chứng phát hành có thể chạy song song sau khi baseline kỹ thuật ổn định. Không bắt phát hành trước khi học được từ công việc thật.

### W0 — Chốt baseline và danh sách gate duy nhất

**Công việc**

- Tạo tài liệu triển khai tiếng Việt tại `E:/DEV/Codex-web/docs/research/260907_CODEX_WEB_OUTCOME_EFFICIENCY_IMPLEMENTATION_PLAN.md` từ kế hoạch được duyệt; dùng chính tài liệu này để theo dõi các chặng, không thêm hệ thống quản trị.
- Lập bảng G0–G10 gồm: mục tiêu, hiện trạng, bằng chứng, phần thiếu, người có quyền đóng và hành động tiếp theo.
- Ghi source HEAD, fingerprint phạm vi, mốc snapshot ledger/projection, producer/schema version và giới hạn số liệu. Giữ JSON đầu vào nguyên trạng.
- Với runtime hiện tại, dùng Recovery Host và connector chính thức xác định gate của epoch đang mở. Nếu chỉ thiếu current-process discovery hoặc compatibility bootstrap hợp lệ, hoàn thiện đúng đường đó rồi ACK có kiểm tra.
- Chỉ activation/restart khi receipt cho thấy thực sự cần, đúng phạm vi được cấp quyền. Giữ nguyên stale candidate chưa đủ điều kiện xử lý.

**Nghiệm thu**

- Có baseline source/proof/acceptance/runtime không mâu thuẫn, hoặc blocker được chỉ rõ bằng receipt.
- Một receipt cũ, `UNCHANGED_ACKNOWLEDGED` hoặc SHA bằng nhau không được dùng thay freshness của epoch hiện tại.
- Không làm mất `.coding-tools`, không thay đổi source ngoài phạm vi.

### W1 — Sửa dứt điểm liên kết proof, cache và acceptance

**Công việc**

- Giữ nguyên hành vi cùng WAVE: cache hit tiếp tục dùng proof ID hiện có.
- Với cache hit sang WAVE khác, tạo **receipt tái sử dụng thuộc RUN/WAVE hiện tại**, tham chiếu proof nguồn, giữ exact input fingerprint, đánh dấu không thực thi lại và duration thực thi bằng 0.
- Làm idempotent việc tạo receipt: quan sát hoặc retry cùng một yêu cầu không tạo nhiều proof tái sử dụng trùng nhau.
- Dùng cùng phép tính fingerprint canonical cho execution summary, completion report và accepted checkpoint; không giữ hai giá trị khác nghĩa nhưng cùng tên.
- Không nới điều kiện cache. Việc tách identity dùng để quy thuộc RUN/WAVE khỏi đầu vào quyết định tính hợp lệ chỉ thực hiện khi có test chứng minh không làm rộng phạm vi tái sử dụng.

**Nghiệm thu**

- Chuỗi `proof đạt ở WAVE 1 → cache hit ở WAVE 2 → acceptance của WAVE 2` hoạt động mà runner chỉ chạy một lần.
- Source, command, cấu hình, môi trường hoặc contract liên quan thay đổi phải làm mất hiệu lực reuse theo hợp đồng.
- Proof lỗi, proof khác workspace hoặc thiếu nguồn gốc không trở thành bằng chứng đạt.
- Không sửa checkpoint hay proof lịch sử để che khác biệt.

### W2 — Đưa điều kiện hoàn thành lên trước thực thi

**Công việc**

Bổ sung một projection `completion_readiness` vào đường prepare/run hiện có, lấy từ chính các validator đang bảo vệ execution và acceptance:

- Workspace, Problem Revision, phạm vi hiểu và phạm vi được sửa.
- Nguồn gốc file hiện có và file dự kiến được thay đổi.
- Interpreter/tool kiểm chứng khả dụng, working directory đúng, verification mode và command thực sự sẽ dùng.
- Các yêu cầu proof, build/artifact và bằng chứng nghiệm thu còn thiếu.

Phân biệt rõ:

- **Môi trường chưa chạy được:** thiếu interpreter, thiếu pytest, target không hợp lệ.
- **Oracle đã chạy và tái hiện lỗi sản phẩm:** trường hợp hợp lệ cho bugfix.
- **Verification đã đạt:** bằng chứng sau sửa.
- **Kết quả nghiệp vụ được xác nhận:** không được suy ra từ build/test chung.

Không đảo Boolean `strong_oracle` một cách máy móc: failing baseline có thể là oracle tốt; lỗi thiết lập môi trường thì không.

Tách phần verification cần tiếp tục theo các bước hiện có — check, test, build, artifact — để lỗi ở bước sau không bắt chạy lại bước trước còn hợp lệ. Completion packet trả gọn: đã thực hiện gì, proof nào còn giá trị, thiếu gì và đúng hành động tiếp theo.

**Nghiệm thu**

- Các ca thiếu môi trường, thiếu verification bắt buộc hoặc thiếu provenance đã biết được báo trước khi trả chi phí triển khai.
- File thay đổi sau prepare vẫn bị phát hiện khi recheck trước ghi/nghiệm thu.
- Không tự nhận toàn bộ dirty worktree vào scope; không tự cấp quyền hay tự accept.
- Build pass không đủ đóng yêu cầu nghiệp vụ khi criterion cần oracle khác.

### W3 — Sửa đường quan sát và định vị mã bằng thay đổi nhỏ

**Quan sát**

- Dùng cùng predicate cho “sự kiện có ý nghĩa được trả về” và “sự kiện đánh thức bounded wait” của bridge.
- Báo rõ cursor đã vượt phần lịch sử còn lưu; không trình bày lịch sử bị mất như trạng thái không đổi.
- Giữ cursor độc lập theo consumer và identity của thread/turn/job.
- Tận dụng paging, wait và resume hiện có trong phản hồi hướng dẫn. Không thêm giao thức event bus hoặc công cụ công khai mới.

**Semantic localization**

- Giữ public contract tối đa 12 query.
- Chia native request thành nhóm tối đa 8, chạy **tuần tự trong cùng admission/resource lease**, giữ thứ tự và query identity.
- Nhóm lỗi chỉ fallback cho phần chưa được xử lý; không làm rơi truy vấn hoặc biến fallback thành semantic success.
- Áp dụng một ngân sách thời gian tổng cho request, không để hai nhóm làm nhân đôi thời gian chờ tối đa.
- Đo đủ điều kiện semantic, thời gian tới bằng chứng liên quan đầu tiên và số lần fallback; không dùng tỷ lệ 6/8.774 của lịch sử để kết luận implementation mới hiệu quả.

**Nghiệm thu**

- Wait thức dậy khi có sự kiện có ý nghĩa, không chờ hết timeout vô ích.
- Cursor hết hạn trả chỉ dẫn refresh đúng identity.
- Request 9–12 query không bị cả batch rơi về fallback chỉ vì giới hạn native.
- Hủy, timeout và lỗi provider đều giải phóng resource claim.

### W4 — Đo đúng chi phí của một Problem, gồm cả các lần không thành công

**Công việc**

Mở rộng reporter và event hiện có, không thêm warehouse:

1. Giữ accepted-result report cho phân tích cohort accepted.
2. Dùng Problem Revision làm mẫu chính của báo cáo hiệu quả sản phẩm, giữ mọi attempt: accepted, failed, aborted, blocked, timeout, chưa kết thúc và reopen.
3. Tách chi phí theo sự kiện có thẩm quyền:
   - trước nghiệm thu kỹ thuật;
   - quan sát/xác nhận sau nghiệm thu;
   - làm lại sau same-revision reopen;
   - quan sát về sau không thuộc quá trình giải quyết.
4. Lấy thời gian chủ động từ hợp các interval đã quan sát; tránh cộng trùng tác vụ lồng nhau và không cộng khác clock domain.
5. Áp dụng kiểm tra exact attribution nhất quán cho cả báo cáo RUN và Problem. Không dùng “lệnh cuối”, thời điểm gần nhau hoặc chỉ có ID trong payload để suy ra liên kết.
6. Giữ thống kê đầy đủ của cohort đã chọn khỏi phụ thuộc cửa sổ rolling `run_metrics`; lưu bằng chứng cần thiết qua cơ chế ledger/receipt hiện có, có giới hạn và không chứa nội dung nhạy cảm.

Định nghĩa “làm lại không cần thiết” được chốt thành các loại có bằng chứng: lặp yêu cầu chắc chắn bị từ chối khi điều kiện không đổi; chạy lại proof còn hợp lệ; khởi chạy lại hành động đã thực hiện; đọc lại cùng dữ liệu không có thay đổi phục vụ quyết định. REPLAN hợp lý, từ chối bảo vệ đúng và sửa lỗi thực sự không tự động được tính là lãng phí.

**Nghiệm thu**

- Một lần đọc RUN sau khi accepted không làm tăng chi phí hoàn thành lần đầu.
- Reopen giữ nguyên Problem Revision và cộng đúng các lần sửa tiếp.
- Tổng các nhóm đo được đối soát được trong cùng population/version; phần không phân loại được công khai là unknown.
- Token, bytes, estimated gap, chi phí theo bảng giá và provider billing được báo riêng.
- Thiếu accounting của host giữ `unsupported/unknown`, không scrape UI hoặc ước lượng thành billing.

### W5 — Chứng minh một công việc HR/PFM thật xuyên suốt hai phiên

**Cách chọn**

Dùng yêu cầu HR/PFM thật tiếp theo do anh giao, có phạm vi và oracle rõ, nằm ngoài việc tự sửa nền tảng Codex-web. Không tự tạo bài toán nghiệp vụ hoặc workload để đủ mẫu.

**Luồng bắt buộc**

- Chốt desired outcome, criterion, invariant, phạm vi loại trừ và phép thử có thể bác bỏ kết luận “đã xong”.
- Gắn đúng Problem Revision → RUN/WAVE → proof → accepted checkpoint.
- Tiếp tục công việc ở phiên/client khác bằng capsule và identity hiện có; quan sát job cũ thay vì khởi chạy trùng.
- Tiếp nhận phản hồi thực tế:
  - đúng yêu cầu: lấy outcome receipt độc lập qua đường được hỗ trợ;
  - vẫn lỗi: reopen cùng revision;
  - yêu cầu thay đổi: chỉ tạo revision mới khi contract thực sự thay đổi.

**Nghiệm thu**

- Anh không phải kể lại toàn bộ yêu cầu hay nối lại identity thủ công.
- Không mất criterion, không dùng proof cũ sai phiên bản, không duplicate write/job.
- Oracle ở đúng tầng nghiệp vụ/tích hợp/UI của yêu cầu.
- Truthful reopen chứng minh continuity trung thực, **không được tính là kết quả đã giải quyết thành công**.

### W6 — Thu cohort tự nhiên và chọn tối đa hai can thiệp có giá trị nhất

**Công việc**

- Thu các Problem liên tiếp theo thứ tự đã đăng ký, checkpoint ở 5 rồi 10; giữ cả ca không thành công.
- Có HR/PFM và Codex-web, báo riêng từng workspace/task class trước khi tổng hợp.
- Giữ gate continuity hiện hành, bao gồm yêu cầu các ca cross-session thực sự đạt; không dùng số lượng 10 để thay bằng chứng continuity còn thiếu.
- Xếp tổn thất theo thời gian chủ động đo được, số thao tác lặp và công sức người dùng.
- Chọn tối đa hai can thiệp trong các khả năng đã có: admission/completion guidance, resume, observation, localization hoặc context reuse. Nếu đồng hạng, chọn phương án ít mã và ít trạng thái hơn.

**Kinh nghiệm lịch sử có điều kiện**

Chỉ khi cohort cho thấy việc lặp lại nguyên nhân đã biết là tổn thất đáng kể, bổ sung tối đa ba case note qua context/capsule hiện hữu. Mỗi note gồm nguyên nhân đã xác minh, điều kiện áp dụng, liên kết phải kiểm tra lại, bước tối thiểu, cách sửa từng thất bại và điều kiện không áp dụng.

Không nạp transcript dài, không chạy lại lệnh lịch sử vô điều kiện, không thêm vector database hay authority mới. Hướng này phù hợp với nguyên tắc target-bound reuse của [Beyond Retrieval](https://arxiv.org/abs/2608.12847); lợi ích của bài báo không được dùng thay benchmark Codex-web.

**Nghiệm thu**

- Có quyết định dựa trên tổn thất đo được, không dựa trên việc tính năng đã tồn tại.
- 5–10 ca chỉ đóng phần feasibility/measurement, chưa đóng tuyên bố cải thiện nhân quả.

### W7 — Thí nghiệm đúng đơn vị Problem trước khi công bố hiệu quả

Có một khoảng trống cần xử lý trước thí nghiệm cấp Problem: P5 hiện dùng `stable_task_assignment`, binding một assignment với một RUN/WAVE và outcome theo acceptance. Nó chưa đủ chứng minh một Problem qua nhiều attempt luôn giữ cùng nhánh.

**Thay đổi có giới hạn, chỉ sau W5–W6**

- Version hóa manifest/assignment contract trong P5 hiện có để gắn một assignment với exact workspace + Problem Revision.
- Cho phép các attempt tiếp theo được nối bằng receipt append-only vào cùng assignment; không bốc lại nhánh khi retry, đổi phiên hoặc reopen.
- Outcome cấp assignment tổng hợp các attempt tại horizon đã đăng ký, giữ toàn bộ mẫu được phân nhánh trong phân tích ITT.
- Giữ epoch/manifest cũ đọc được và nguyên trạng. Thay đổi schema dùng migration được kiểm thử trong cùng ledger, không thêm database.
- Bổ sung receipt cho active-time, redundant-rework và chất lượng, dẫn về nguồn bằng chứng; không cho các số tổng nhập tay tự trở thành bằng chứng hiệu quả.

**Trình tự**

1. Đóng common baseline an toàn cho cả hai nhánh.
2. Chạy A/A có quyền mở rõ ràng để kiểm tra assignment, continuity, clock, coverage và analyzer.
3. Đăng ký A/B riêng cho một micro-policy mỗi epoch.
4. Giữ model, route, quyền, proof policy, instrumentation và continuity nền tương đương.
5. Chỉ thay phần can thiệp đang được đánh giá.

Các sửa lỗi correctness/authority thiết yếu được áp dụng cho cả hai nhánh; không giữ nhánh đối chứng có lỗi đã biết chỉ để tạo mức cải thiện đẹp.

### W8 — Đường phát hành thống nhất và quyết định KEEP / MODIFY / REMOVE

**Phát hành**

- Bổ sung một entrypoint ứng viên phát hành mỏng, gọi các lane hiện có: Node, Python MCP, packaging và packaged smoke; không chạy trùng cùng bộ proof trong một candidate.
- Giữ `dist` là thao tác đóng gói, nhưng không coi chạy `dist` riêng là đủ chứng nhận release candidate.
- CI vẫn kích hoạt thủ công theo chính sách hiện hành; đồng bộ đường Desktop với test runner Python chính thức và entrypoint candidate. Rust chỉ chạy khi boundary liên quan yêu cầu.
- Receipt ứng viên gắn exact source, toolchain, proof, artifact hash và kết quả smoke.
- Kiểm chứng cài đặt trên môi trường cô lập; sau đó Windows sạch/máy mới, login/session và Recovery. Upgrade chỉ được kiểm chứng từ installer lịch sử có thật, không tạo tiền nhiệm giả.
- Không publish, tag hoặc deploy trong bước chuẩn bị này.

**Đơn giản hóa**

- **KEEP:** single Runtime, workspace isolation, write fencing, exact proof, PRL/outcome, Recovery và canonical ledger.
- **MODIFY:** những đoạn gây chi phí lặp có bằng chứng trong chương trình trên.
- **REMOVE:** chỉ loại bỏ projection, wrapper hoặc micro-policy dư thừa đã được chứng minh không còn vai trò riêng. Không xóa bằng chứng.
- Automatic routing, auto-handoff và global server-first tiếp tục OFF cho đến khi từng chính sách có gate riêng đạt và có quyền bật rõ ràng.

## 3. Hợp đồng API, dữ liệu và tương thích cần giữ

| Bề mặt | Thay đổi dự kiến | Ranh giới bắt buộc |
|---|---|---|
| `agent_workflow` prepare/run | Bổ sung `completion_readiness`, kế hoạch verification và phần thiếu được suy ra từ validator hiện có. | Không thêm public tool; không tự nhận dirty files hoặc cấp quyền. |
| Proof và completion report | Receipt reuse thuộc WAVE hiện tại, lineage về proof nguồn, fingerprint canonical thống nhất; trạng thái executed/reused/failed/missing rõ ràng. | Không biến reuse thành lần thực thi mới; không thay proof lịch sử. |
| Observation | Bổ sung metadata khoảng cursor còn lưu và mất lịch sử; giữ bounded wait và continuation. | Không trả dữ liệu khác consumer/workspace; không thêm quyền từ observation. |
| Economics | Nhóm vòng đời, exact attribution, completeness và Problem-level denominator. | Trường mới có version; lịch sử thiếu bằng chứng giữ unknown, không backfill theo suy đoán. |
| P5 cấp Problem | Assignment bất biến theo revision, nhiều attempt receipt, outcome/analysis receipt theo horizon. | Chỉ mở trong epoch mới; old manifest không được diễn giải lại; không tự activation/promotion. |

Các tên lỗi hiện hành là authoritative; không khôi phục alias lịch sử chỉ để khớp bản phân tích.

Command, credential hoặc nội dung người dùng không được đưa nguyên dạng vào telemetry/completion packet. Dùng identity, hash, trạng thái và tham chiếu đã được lọc.

## 4. Kiểm thử và tiêu chí chứng minh hiệu quả

### Kiểm thử kỹ thuật bắt buộc theo thay đổi

- **Proof:** same-wave/cross-wave reuse, idempotent receipt, fingerprint equality, invalidation, foreign workspace, failed proof, acceptance và Problem coverage.
- **Readiness:** thiếu interpreter/module, target sai, oracle lỗi thật, test pass nhưng thiếu build/artifact, provenance thay đổi sau prepare.
- **Observation:** meaningful-event wake, timeout thật, cursor eviction, paging tiến triển, hai consumer độc lập, reconnect, cancellation và không tạo job trùng.
- **Semantic:** 1/8/9/12 query, index mapping, partial failure, admission denial, deadline tổng, release claim, không lộ secret.
- **Economics:** late observation, reopen, nhiều RUN/WAVE, overlapping spans, different clocks, missing usage, duplicated event, attribution sai và expected guard rejection.
- **Continuity/P5:** cùng revision qua phiên/retry vẫn cùng assignment; giữ mọi outcome; không reseed, không crossover; replay analyzer có kết quả xác định; migration bảo toàn lịch sử.
- **Release:** source/artifact drift phải fail, proof bắt buộc thiếu phải fail, packaged/installed Recovery không ảnh hưởng runtime đang dùng.

Trong khảo sát đã chạy `test_proof_ledger.py` và `test_pytest_selector_paths.py`: **6 passed, 1 skipped, 47 subtests passed**. Diagnostic ledger tạm đã tái hiện cross-wave receipt gap và fingerprint mismatch. Đây chưa phải proof của bản sửa.

### Hợp đồng đo hiệu quả được chốt

**Đơn vị mẫu:** một Problem Revision, không phải mỗi RUN/WAVE.

**Hai mục tiêu phải đồng thời đạt:**

- Tỷ số p90 thời gian chủ động treatment/control ≤ **0,80**.
- Tỷ số số thao tác làm lại không cần thiết trên mỗi Problem treatment/control ≤ **0,70**.

Thời gian chủ động bao gồm các attempt cần thiết tới kết quả đáng tin, kể cả sửa tiếp sau reopen trong cửa sổ đã đăng ký; không chỉ dừng ở acceptance đầu tiên. Thời gian chờ người dùng, wall time và quan sát ngoài quá trình giải quyết được báo riêng.

**Điều kiện bảo vệ**

- Không vi phạm authority, sai workspace, mất dữ liệu, duplicate mutation hoặc false closure nghiêm trọng.
- Tỷ lệ kết quả được xác nhận, reopen và công sức can thiệp không được xấu đi.
- Không bỏ ca thất bại hoặc thiếu outcome khỏi denominator.
- Không lấy missing token/cost làm zero; không công bố tiết kiệm tiền khi coverage chưa đủ.

**Cách kết luận**

- Dùng cohort đầu để xác định phân bố, mức thiếu dữ liệu và feasibility; không dùng chính nó làm bằng chứng thắng A/B.
- Trước mở A/B, khóa horizon, follow-up, cỡ mẫu, strata, analyzer, ngưỡng chất lượng và cách xử lý missing/censored outcomes.
- Cỡ mẫu được tính từ pilot cho cả hai endpoint, với power mục tiêu 80% và mức tin cậy 95%; lấy yêu cầu lớn hơn. Không mặc định 10 ca là đủ.
- Để tuyên bố chắc chắn đạt ngưỡng, khoảng tin cậy phải hỗ trợ cả hai mức cải thiện đã chọn; chỉ đạt point estimate được báo là tín hiệu, chưa đóng gate.
- Không dừng sớm vì kết quả tạm thời đẹp. Thiếu dữ liệu, baseline redundant-rework bằng 0 hoặc khác biệt task mix không kiểm soát được thì giữ kết luận chưa đủ bằng chứng.
- Nếu không đạt, sửa/thu hẹp/bỏ micro-policy đang thử; không thêm tầng AI để bảo vệ thiết kế.

Cách đo này cũng giữ đúng cảnh báo của [Measure Before You Manage](https://arxiv.org/abs/2608.31057): giảm context hoặc chi phí quản lý danh nghĩa chưa đồng nghĩa cải thiện kết quả công việc.

### Bảng đóng đầy đủ G0–G10

| Gate | Bằng chứng để đóng |
|---|---|
| G0 — Runtime | Process/epoch/source đúng và connector freshness hợp lệ; ghi rõ compatible hay strict. |
| G1 — Provenance | Exact source/file/proof/acceptance lineage khớp, không nhận nhầm WIP. |
| G2 — Baseline | Baseline tích hợp đã nghiệm thu; những claim live/package được chứng minh riêng. |
| G3 — Lifecycle | Không job/lease/acceptance nguy hiểm chưa giải thích; stale được xử lý đúng authority và ngưỡng hoặc giữ lại có phân loại. |
| G4 — Semantic | Hành vi truy vấn thật đúng, hoặc fallback có bằng chứng và giới hạn rõ; availability không thay efficacy. |
| G5 — Accounting | Từng plane được đo và quy thuộc đúng; full accounting chỉ đóng khi có nguồn host/provider thực sự hỗ trợ. |
| G6 — Continuity | Một Problem thật đi qua phiên, không mất state/duplicate work; kết quả xác nhận hoặc reopen đúng. |
| G7 — Natural cohort | Cohort liên tiếp có provenance, đủ continuity theo gate hiện hành, giữ ca không thành công. |
| G8 — Economics | Đo đúng Problem, mọi attempt, cửa sổ thời gian và coverage; không thiên lệch accepted-only. |
| G9 — Experiment | A/A hợp lệ, A/B preregistered, đạt hai mục tiêu cùng quality floor; chưa đạt thì không promotion. |
| G10 — Simplification | Mỗi cơ chế có disposition và bằng chứng; không gọi DEFER là efficacy PASS. |

## 5. Tổ chức thực hiện, quyền hạn và điều kiện kết thúc

- Một controller chịu trách nhiệm contract, tích hợp, authority và nghiệm thu cuối. Các nhánh chỉ song song khi khác phạm vi; không có hai writer cùng sửa một file.
- W1–W2 là một chuỗi phụ thuộc. W3 và nhánh release có thể độc lập sau khi interface chung ổn định. W4 phải xong trước khi dùng số liệu để nghiệm thu hiệu quả.
- Kết thúc mỗi chặng phải báo: đã làm gì, Git/RUN hiện tại, proof mạnh nhất, blocker, phần còn lại và đúng bước tiếp theo.
- Không rerun toàn bộ suite sau mỗi thay đổi nhỏ. Chạy focused test trước; affected-boundary/integration và release gate một lần tại fingerprint tích hợp phù hợp.
- Mọi thay đổi trên HR/PFM cần một yêu cầu nghiệp vụ và phạm vi riêng. Việc chọn HR/PFM làm cohort không cấp quyền sửa dữ liệu nghiệp vụ, migration, IAM hoặc production.
- Mở P5, dùng provider trả phí, activation/restart, cài đặt máy thử, commit/push/release/deploy là các ranh giới quyền riêng. Trước mọi commit/push phải chạy staging và delivery guard của `.coding-tools` theo AGENTS.
- Tài liệu nghiên cứu cũ và JSON đầu vào giữ nguyên. Chỉ cập nhật hướng dẫn hiện hành và thêm bằng chứng mới có mốc quan sát.

**Trạng thái bàn giao của lượt lập kế hoạch:** chưa sửa source hay tạo tài liệu triển khai trên đĩa vì đang ở Plan Mode; không commit/push, mở thí nghiệm, restart, ACK, cài đặt hoặc phát hành. HEAD vẫn `cd53817`; thay đổi đồng thời ở `package.json`, hai script ledger và JSON đầu vào được giữ nguyên, không được nhận vào phạm vi của lượt này. Kiểm tra diff/whitespace không báo lỗi hoặc conflict. Các kiểm tra ledger sản phẩm đều chỉ đọc; diagnostic ghi dữ liệu chỉ trong thư mục tạm cô lập.

**Bước triển khai đầu tiên là W0 rồi W1**, không phải xây thêm router hay bộ nhớ. Chương trình chỉ được gọi là hoàn thiện toàn diện khi cả ba mức nghiệm thu anh đã chọn có bằng chứng; một baseline xanh, một báo cáo hoàn thành hay một installer chạy được không thay thế các gate hiệu quả và kết quả người dùng còn mở.
<!-- END ATTACHED PLAN -->

## Checkpoint triển khai 01 — 07/09/2026 12:35–12:38 +07:00

Người dùng đã chuyển yêu cầu từ lập kế hoạch sang triển khai toàn bộ chương trình. Mục tiêu W0–W8/G0–G10 giữ nguyên. Đây là tiến triển W0 chỉ đọc, không phải W0 hoàn tất hoặc source acceptance.

Bằng chứng: [260907_CODEX_WEB_W0_READONLY_BASELINE.json](260907_CODEX_WEB_W0_READONLY_BASELINE.json), HEAD 24186fefbdbb9c1dca450ae5e96df167be93c87e.

- Active snapshot và archive: integrity ok, foreign-key violations 0; archive khớp manifest hash/size/run count/run IDs và không thay đổi trong lúc đọc. Không trùng ID RUN/WAVE/proof/checkpoint; distinct tương ứng 1391/2065/2252/671. Chưa kiểm toán toàn bộ cross-shard causal joins/event chains nên chưa coi history economics đầy đủ.
- Không managed job hoặc unbound live resource; 36 RUN là THRESHOLD_SENSITIVE_STALE_CANDIDATE, sáu P5 anchors. Không reconcile/terminalize chúng.
- Projection drift đã được phân biệt: task-state trỏ RUN 037b642a187e4f098dc66e6dd1c9b3c1, WAVE 0742b3e58f714d6faac3835471840b1b, ABORTED; active ledger không có RUN này. Helper locate xác nhận RUN ở archive, status stale. Đây là khoảng hở archive-aware observation cần xử lý trong W0/W4; không sửa thủ công task-state hoặc copy RUN về live ledger.
- dev:status mới: Electron STALE/update_pending, MCP current, fully_ready=false/runtime_update_incomplete=true; connector UNCHANGED_ACKNOWLEDGED nhưng không có freshness mode/current-process rediscovery. Không restart/ACK trong lượt này.
- Blocker của implementation writer: catalog không có Coding Tools MCP workspace_context/task_control, resources/templates rỗng; chưa thể lấy write lease hoặc accept/reject qua surface hỗ trợ. Theo sol-lean-codex/eocl-runtime, không tự thay quyền này bằng direct source write hay raw protocol. Chưa tạo RUN/WAVE canonical hoặc nhận mình có lease.
- Thay đổi lượt này chỉ là evidence JSON và checkpoint tài liệu; ledger dirty từ trước giữ nguyên. Không product source, test source, commit/push, provider dispatch, experiment, service/install/release/deploy.

Bước tiếp theo: khôi phục Coding Tools MCP được hỗ trợ trong phiên; recapture context/authority rồi nhận W1 exact scope. Xử lý archive-aware observation bằng kiểm thử âm/dương đúng boundary trước khi gọi W0 hoàn tất. Không đánh dấu toàn goal blocked ở lần gặp blocker đầu; toàn objective vẫn active, các gate empirical/external không bị thu hẹp.

## Checkpoint triển khai 02 — 07/09/2026 12:39 +07:00

Bằng chứng mới: [260907_CODEX_WEB_W0_LINEAGE_AUDIT.json](260907_CODEX_WEB_W0_LINEAGE_AUDIT.json). Active snapshot SHA-256 trùng checkpoint 01; manifest/archive ổn định trong cửa sổ đọc.

- Kiểm tra hash chain bằng hàm canonical verify_chain trên LedgerFacts chỉ đọc: active 273 RUN/9113 event và archive 1118 RUN/34000 event đều không có chain failure. Tổng 1391 RUN/43113 event.
- Các kiểm tra structural reference không phát hiện missing RUN/WAVE/delegation/parent delegation/upstream proof; proof/checkpoint đều có wave owner đúng RUN.
- Một event lịch sử terminal_parent_lane_reconciled ngày 23/08 có event.run_id khác owner của event.wave_id. Hash chain vẫn hợp lệ. Giữ nguyên lịch sử; reporter W4 phải đánh dấu semantic attribution chưa đủ, không ghép theo wave_id hoặc timestamp để tạo chi phí exact. Chưa kết luận nguyên nhân producer hoặc tính hợp lệ nghiệp vụ chỉ từ kiểm tra khóa.
- Scope kiểm tra không bao gồm mọi tham chiếu bên trong metadata/payload hoặc kết quả nghiệp vụ; không gọi đây là proof toàn bộ economics/Trusted Resolution.
- Recheck catalog/resources/templates vẫn không có Coding Tools MCP. Implementation writer vẫn thiếu supported lease/acceptance surface; đây là lần thứ hai blocker lặp lại, nhưng lượt này có tiến triển bằng chứng W0. Không tạo writer/RUN, không sửa source/ledger, không restart/ACK hay bật experiment.

Hành động tiếp theo vẫn là khôi phục supported Coding Tools MCP để cấp lease và triển khai W1; không tiếp tục quét rộng lịch sử chỉ để tạo thêm báo cáo. Toàn mục tiêu còn active, chưa có source fix hoặc acceptance mới.

## Checkpoint triển khai 03 — 07/09/2026 13:18–13:36 +07:00

Đã hoàn thành và kiểm chứng W1, W2, W3 và W4 ở phạm vi source/test; đây không phải EOCL acceptance, current-process connector rediscovery, outcome người dùng, release hay deployment proof.

- **W1 — proof/acceptance:** cache hit cross-WAVE tạo một receipt passed thuộc WAVE đích, có `cache_hit=true`, `duration_ms=0`, `upstream_proof_ids` trỏ proof nguồn và `proof_reuse.executed=false`; reuse lặp trong cùng WAVE đích là idempotent. Fingerprint acceptance dùng `passed_proof_fingerprint` canonical, không phụ thuộc thứ tự insert proof.
- **W2 — completion readiness:** `agent_workflow` trả projection v1 không thực thi và không lộ raw command (chỉ SHA-256 command). Trước candidate/model dispatch, nó phân biệt command/interpreter/module/target không sẵn sàng với baseline non-zero tái hiện product oracle; lỗi môi trường bị chặn với `COMPLETION_READINESS_BLOCKED`, không gọi bridge. Readiness không cấp write lease, không nhận toàn dirty worktree, không suy business outcome từ build. Luồng có patch do caller cung cấp vẫn giữ validation hiện hữu và không bị chặn nhầm như một lần dispatch model.
- **W3 — observation/semantic:** meaningful-event predicate dùng chung cho lọc observation và wake; cursor bị eviction trả `history_gap`/`history_floor_cursor`. Native LSP tối đa 12 query chạy 8+4 tuần tự trong một claim và deadline chung 35 giây; chỉ unresolved query của batch lỗi/timeout fallback text search, index gốc được giữ.
- **W4 — economics:** schema economics v7 và journey v2 buộc attribution chính xác `Problem Revision → RUN → eligible WAVE`; events wrong-WAVE/partial không được tổng hợp thành total giả. Tổng token/money giữ PARTIAL/UNOBSERVED khi thiếu coverage; topology/clock/acceptance/reopen không bị gộp theo timestamp gần nhau.

Validation tại HEAD `24186fefbdbb9c1dca450ae5e96df167be93c87e` (source worktree còn uncommitted):

- `python -B -m pytest tests/ -q -p no:cacheprovider`: **960 passed, 5 skipped, 226 subtests** trong 381,03 giây.
- Focus W2 mới: prepare readiness hash-only, baseline setup failure không dispatch bridge, missing command không dispatch bridge, product-oracle non-zero vẫn được route candidate: **4 passed**.
- `python resources/coding-tools-mcp/scripts/check_module_size.py`: passed; `workflow_tools.py` còn 1.598 dòng dưới budget 1.600.
- `python -m py_compile coding_tools_mcp/completion_readiness.py coding_tools_mcp/workflow_tools.py` và `git diff --check`: passed/clean.

Trạng thái authority/runtime:

- Session hiện tại không có Coding Tools MCP public surface callable, do đó không có write lease, EOCL accept/reject, `tools/list`, `server/discover`, connector rediscovery hoặc runtime restart mới nào được thực hiện/ghi nhận.
- Tab Coding-VP Live của dự án có thể đọc, nhưng chưa gửi message/tool call nào trong checkpoint này. Không lấy trạng thái/báo cáo lịch sử hiển thị trên tab làm receipt discovery mới.
- Ledger và README đang dirty cùng những source/test W1–W4; không reset, không sửa ledger thủ công, không stage/commit/push. Trước mọi commit/push trong tương lai phải chạy `npm run stage:coding-tools-delivery`, `npm run check:coding-tools-delivery`, rồi `git diff --cached --check`.

Điều kiện tiếp theo không thể tự tạo bằng source: cần thực hiện discovery chỉ-đọc qua Coding-VP Live và sau đó một Problem HR/PFM thật có oracle/kết quả độc lập hoặc same-revision reopen (W5). Cohort tự nhiên W6, P5/W7, và W8 package/new-machine/upgrade proof tiếp tục giữ mở; không synthetic workload, không tự bật routing/promotion, không release/deploy.

## Checkpoint triển khai 04 — 07/09/2026 13:43–14:00 +07:00

Đã bổ sung evidence runtime/package trong phạm vi có thể kiểm chứng; không gọi đây là closure của W5–W7, G0–G10, release hay production.

### Coding-VP Live: discovery và stale-run audit chỉ đọc

- Discovery mới trên đúng workspace `E:\DEV\Codex-web` trả `smart-v3`, đúng tám public tool (`workspace_context`, `agent_workflow`, `task_control`, `document_workflow`, `exec_command`, `command_control`, `request_permissions`, `view_image`) và contract SHA-256 `6420537a2150a7d8e0152eabde4b298c3c689645a4515ba17fd254d60fc43cdf`. Đây là bằng chứng public surface callable, không phải strict connector rediscovery receipt.
- `workspace_context` quan sát được tại thời điểm discovery: `main`, HEAD `24186fefbdbb9c1dca450ae5e96df167be93c87e`, runtime `1.0.0`, activation epoch `activation-mtqv8p56-eb674b129409ea19ece3428ee0ed6fbe`; `task_control(get)` quiescent với claim/command/heavy/orphan đều bằng 0. Semantic localization vẫn fail-closed vì `NATIVE_LSP_BINDING_INVALID` (thiếu `origin` và `credential_file`); không tạo credential hoặc đổi binding.
- Census cuối trả 31 stale/unresolved RUN, global live job/claim bằng 0. Exact audit chỉ đọc được 21/31 RUN trước khi safety layer chặn audit read-only của RUN kế tiếp; không retry bằng mutation hay suy diễn dữ liệu thiếu.
- 19 RUN (`73e2…`, `51ca…`, `ce16…`, `1ee4…`, `39c8…`, `dccd…`, `29ea…`, `adf1…`, `ccf1…`, `bb20…`, `8661…`, `3d86…`, `6cae…`, `8440…`, `b47a…`, `af84…`, `eb18…`, `d68f…`, `410d…`) đã có evidence `active/PREFLIGHT`, lease/owner rỗng, không job/claim/lane sống và không P5/semantic exception hiển thị. Chúng chỉ là candidate cho **fresh exact preflight** sau khi canonical MCP đã stopped; chưa RUN nào đủ điều kiện mutation ngay.
- `9b50ea48…` phải HOLD vì Problem revision/handoff continuity còn `OPEN`; `1977b099…` phải HOLD vì `REPLAN` với `NOT_ACCEPTED_REPLAN_REQUIRED`/`PROMPT_TOO_LARGE`. 10 RUN còn lại (`75f7…`, `c6bd…`, `6120…`, `7cd8…`, `9515…`, `f995…`, `9f0e…`, `fc2e…`, `a46c…`, `9492…`) là UNKNOWN vì chưa có exact fence/semantic audit.
- Không có `task_control reconcile` trực tiếp. Nếu một đợt được phê duyệt riêng sau này, mỗi transaction tối đa 16 exact lowercase-hex IDs, đi qua `restart_runtime` full-clean; từng ID cần preflight mới với physical + logical SHA-256, `--runtime-stopped`, reconcile tuần tự và receipt `schema_version=1`, `chain_ok=true`, `RECONCILED_STALE`. Không có bulk DB update, ACK hoặc restart trong checkpoint này.

### W8 package/recovery: helper runtime bắt buộc đã được đưa vào tree đóng gói

- Xác nhận defect source: `FullCleanActivation` gọi `resources/coding-tools-mcp/scripts/reconcile_exact_stale_run.py`, nhưng `extraResources` trước đó loại toàn bộ `coding-tools-mcp/scripts/**`; packaged full-clean sẽ dừng fail-closed với `EXACT_STALE_RUN_HELPER_UNAVAILABLE` nếu đi vào seam này.
- `package.json` giờ vẫn giữ deny-list toàn bộ scripts dev, nhưng thêm FileSet riêng chỉ cho `reconcile_exact_stale_run.py`. `scripts/verify-packaged-resources.js` chỉ cho phép traversal thư mục này và đúng một helper; mọi script khác tiếp tục bị sanitation reject. `scripts/packaged-recovery-smoke.js` yêu cầu helper tồn tại.
- Focused Node proof: `node --test tests/build-verification.test.js tests/full-clean-activation.test.js` = **52 passed, 0 failed**. Test khẳng định FileSet chính xác, source/packaged exact projection, helper được phép, và `report_runtime.py` vẫn bị reject.
- Package directory build cô lập bằng electron-builder đã PASS. Packaged helper có SHA-256 `4a4983102e9efde8fc803b33348d3f8488afc01e78d8519224f742dbe91bb3b2`, trùng source. `node scripts/packaged-recovery-smoke.js` trên output đó PASS: app/asar/resource presence, smart-v3 eight-tool contract, Recovery Host + independent Recovery MCP, supervisor healthy, isolated user-data, fail-closed live-owner/hash checks và không Scheduled Task mutation.
- Smoke chỉ tạo Recovery Host tạm trong isolated user-data rồi tự cleanup; không build NSIS installer, không install/upgrade/rollback/new-machine test, release, push, deploy hoặc restart runtime đang vận hành. Output package tạm hiện còn tại `C:\Users\Admin\AppData\Local\Temp\codex-web-package-proof-20260907-01` vì policy môi trường chặn lệnh xóa recursive trước khi thực thi; không nằm trong repository và có thể được xóa sau bằng thao tác được phép.

**Trạng thái hiện tại:** W1–W4 có source/test proof từ checkpoint 03; seam W8 packaged-helper có source + focused Node + real packaged smoke proof ở worktree dirty. Chưa có EOCL acceptance cho W1–W4, strict connector rediscovery, live LSP binding, full installer/new-machine/upgrade/rollback evidence, natural HR/PFM Problem W5, cohort W6, P5 A/A–A/B W7, outcome/effectiveness, release hay deployment. Git chưa commit/push; ledger và toàn bộ `.coding-tools` evidence phát sinh được giữ nguyên.

**Bước kế tiếp:** không động stale RUN cho tới khi exact fresh preflight hợp lệ được thu qua supported full-clean transaction và quyết định operational riêng. Để tiến tới G6–G9, cần một yêu cầu HR/PFM thật có oracle, Problem Revision và quyền xác nhận outcome; không thể thay bằng workload tạo sẵn. Khi có phạm vi đó, hoàn thiện P5 Problem-Revision multi-attempt binding rồi chỉ mở A/A theo manifest riêng.

## Checkpoint triển khai 05 — 07/09/2026 14:52 +07:00

Đã đóng thêm các lane local có oracle trong khi chờ dữ kiện nghiệp vụ; không dùng dữ liệu lịch sử HR để thay cohort tự nhiên, EOCL acceptance hay outcome độc lập.

### Recovery/package trên source hiện tại

- Sửa `RecoveryPlaneService.stop()` để snapshot cả ba receipt trước khi gọi `ownedIdentity()`, rồi recheck trước terminate/clear. Nếu receipt bị thay bằng một owner khác trong lúc quan sát, thao tác dừng fail-closed với `RECOVERY_PROCESS_STATE_CHANGED`; riêng nhánh stale receipt tự-clear vẫn hợp lệ chỉ khi port đã được chứng minh idle và receipt hiện tại rỗng. Không restart, adopt hay kill runtime đang vận hành.
- `npm test` tại HEAD `24186fefbdbb9c1dca450ae5e96df167be93c87e` PASS: **729 passed, 0 failed**, sau đó `source root clean` và `repository secret check: PASS`. Đây là proof source/test của dirty worktree, không phải acceptance hay release.
- Không dùng `npm run dist:dir` vì lệnh đó xóa `dist/` đang chứa artifact cũ. Đã build `electron-builder --dir --publish never` sang output cô lập `C:\Users\Admin\AppData\Local\Temp\codex-web-package-current-20260907-1217`; executable được tạo và packaged helper SHA-256 là `4a4983102e9efde8fc803b33348d3f8488afc01e78d8519224f742dbe91bb3b2`.
- `CODEX_PACKAGED_APP_ROOT=<output cô lập> node scripts/packaged-recovery-smoke.js` PASS: app/asar và 8 required resources, `smart-v3` eight-tool contract, Recovery Host/MCP isolated healthy, live owner và hash mismatch fail-closed, production descriptor không đổi và không có Scheduled Task mutation. Đây là directory-package smoke của current bytes, chưa là NSIS install/upgrade/rollback/new-machine/release proof.

### Cohort lịch sử HR chỉ-đọc

- Workspace HR quan sát riêng: `E:\DEV\HR STA\HR`, branch `V_Finance`, HEAD `78dc77397cccc90806eb582127b7361280bca596`. Ledger `schema_version=9`, `integrity_check=ok`; snapshot cho thấy 42 RUN/WAVE accepted, 224 active, 36 stale, 18 RUN aborted, 54 WAVE aborted/replanned và còn một controller lease active. Không ghi vào source, database, IAM, runtime hay `.coding-tools` của HR.
- `performance.json` của HR ghi 6.042 tool calls, 268 errors, 1.833 idempotency-eligible calls nhưng chỉ 691 calls có key, 85 proof-cache eligible nhưng 0 hit, 771 fallback searches và không có native-LSP sample; error taxonomy lớn nhất là VALIDATION (121), RUNTIME (58) và AUTHORITY_DENIED (47). Đây là dấu hiệu ưu tiên observation/readiness/semantic fallback, không phải provider billing hoặc business effectiveness.
- HR thiếu bảng `problem_revisions`, performance projection không giữ `run_metrics`, và không có native-LSP sample. Vì vậy nó không tạo được chuỗi exact Problem Revision → attempt → outcome, full resource coverage hay same-source/runtime provenance cần cho W5/G6/G8, P5 promotion hoặc automatic routing. Dữ liệu này chỉ là operational cohort độc lập để đặt ưu tiên; không import vào canonical ledger Codex-web, không tính thành accepted result, không tạo synthetic workload.

**Trạng thái hiện tại:** W1–W4 vẫn ở mức source/focused proof; W8 có thêm package-directory smoke trên bytes hiện tại. Các gate còn mở: EOCL accept/reject, current-process `tools/list`/`server/discover` rediscovery, live semantic binding, một Problem HR/PFM thật có oracle và outcome/reopen, cohort W6, P5 A/A–A/B, installer/new-machine/upgrade proof, commit/push/release/deploy. Không commit, push, publish, deploy hoặc restart service trong checkpoint này; `.coding-tools` và concurrent WIP được giữ nguyên.

## Checkpoint triển khai 06 — 07/09/2026 14:54 +07:00

Recapture query-only xác nhận `.coding-tools` của HR đang biến động do writer hoạt động: `integrity_check=ok`, `schema_version=9`, RUN `accepted=43`, `active=226`, `stale=36`, `aborted=18`; WAVE `accepted=43`, `active=226`, `replanned=42`, `aborted=54`. Projection performance cùng cửa sổ là 6.148 tool calls, 282 errors, 1.899 idempotency-eligible / 700 keyed, 85 proof-cache eligible / 0 hit, 793 fallback searches, 0 native-LSP availability samples và một `run_metrics` record retained. Điều này thay thế snapshot số đếm trong checkpoint 05, không phải bằng chứng cohort: một record không đủ lineage/coverage và HR vẫn không có `problem_revisions`. Không ghi, khóa hoặc làm thay đổi bất kỳ file/lease/RUN/WAVE nào của HR.

## Checkpoint triển khai 07 — 07/09/2026 15:56 +07:00

Đã đọc bổ sung dữ liệu làm việc HR theo query-only. Snapshot ledger nhất quán trong transaction (`data_version` không đổi, `integrity_check=ok`, schema v9) lúc `08:56:24Z`; performance là file projection riêng chốt tại `08:55:47Z`, vì vậy không gộp hai nguồn thành một transaction liên-file.

### Nội dung có thể bổ sung ngay vào W0–W4

- **Baseline kỹ thuật có integrity:** HR có 45 RUN/WAVE accepted và 45 checkpoint accepted; 204 proof gồm 166 passed/38 failed; 969 `observation_span_recorded`; 42 `quality_outcome_recorded`. Các foreign join RUN→WAVE, proof→WAVE và checkpoint→WAVE đều bằng 0 lỗi trong snapshot. Đây là evidence tốt cho execution/proof telemetry, không phải user/business outcome.
- **Outcome vẫn chưa có:** 42 quality events chỉ giữ `oracle_pass` và `source`; key `problem_id`, `problem_revision`, `problem_revision_fp` và `independent_outcome` xuất hiện 0 lần trong event payload. Không có bảng `problem_revisions`; vì thế không truy vết được Natural Problem, reopen hay kết quả độc lập từ HR sang Codex-web.
- **Semantic/readiness baseline:** 144 localization samples/962 queries đều fallback search; native LSP available/attempted/handled đều 0. Đây là baseline hợp lệ để ưu tiên W3 (binding + per-query fallback), nhưng không cho phép tự bật native provider hoặc suy hiệu quả của provider chưa chạy.
- **Cache/idempotency baseline:** proof cache 92 eligible, 0 hit, 92 miss, 0 ms saved; idempotency required 196/196 có key nhưng eligible overall chỉ 554/1.981 có key. Có thể theo dõi hai tỷ lệ này như KPI hoạt động sau khi exact lineage tồn tại; không được gọi 0 cache hit là economic loss hay hiệu quả cải thiện chưa đo.
- **Failure taxonomy:** 316 errors gồm VALIDATION 149, RUNTIME 69, AUTHORITY_DENIED 49, NOT_FOUND 24 và các lớp còn lại 25. Điều này xếp ưu tiên cho completion readiness/validation, recovery và authority UX; không phải phân phối lỗi business hay căn cứ chọn model.
- **Cross-plane observation:** trong cửa sổ phân tích có 159 record ChatWeb host; 38 assistant-first-visible, 38 host-turn-span. Có 31 raw record, tương ứng 10 logical turn/trace identity, đồng thời match ledger. Đây chỉ đủ để thiết kế metric coverage và tách clock domain; phần còn lại không được suy “same turn”, và nhiều renderer clock domain không được cộng thẳng thành TTPR.

### Những gì chưa thể nhận vào W5–W7

- Toàn bộ bảng P5 (`epoch`, enrollment, assignment, protocol, workflow binding, outcome) đều 0 row. Không có arm, ITT, A/A, A/B, efficacy hay promotion data để bổ sung.
- `task-state.json` hiện là projection cũ (`updated_at` 24/08, `waiting/REPLAN`) dù RUN/WAVE nó tham chiếu còn tồn tại active trong ledger. Nó hữu ích để phát hiện projection stale, không được coi là live task state hay outcome.
- `task-history.json` có 100 archived record nhưng chỉ 9 completion report `ACCEPTED`; 83 không có acceptance value. Nó hữu ích cho report-coverage gap, không thay canonical ledger hay independent outcome.

### Candidate intake từ HR source đang làm

Current WIP chia thành ba cụm có thể trở thành **candidate** cho một Natural Problem sau khi người sở hữu nghiệp vụ xác nhận: (1) Core Project API/assignment filtering và archive semantics; (2) Organization Access/Org Chart với redaction, accessibility, canonical assignment và missing-data presentation; (3) Project Finance overview/navigation và map rendering. Test source hiện tại có các assertion fail-closed/redacted/missing-explicit, nhưng các mô tả, ảnh mẫu và trạng thái `[x]` trong `tasks/todo.md` vẫn chỉ là kế hoạch/claim nội bộ. Không dùng KPI, người, số lượng, trạng thái hay ảnh mẫu trong đó làm HR fact, outcome hoặc cohort row nếu chưa có source-backed data binding và independent confirmation.

**Bước tiếp theo bổ sung được khi có một owner nghiệp vụ:** mở một Problem Revision cho đúng một trong ba candidate, ghi source/worktree/runtime/clock identities trước attempt đầu, bind mỗi retry/reopen vào cùng revision, giữ unknown cost/coverage là unknown, rồi nhận xác nhận outcome độc lập hoặc reopen thật. Cho tới thời điểm đó, dữ liệu HR chỉ nâng chất lượng instrumentation và priority; không được import vào ledger Codex-web, mở P5, đổi routing, restart runtime, commit/push hay tuyên bố đạt ngưỡng hiệu quả.
