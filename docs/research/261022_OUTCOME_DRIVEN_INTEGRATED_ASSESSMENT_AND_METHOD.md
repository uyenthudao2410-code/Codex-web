# CODEX-WEB — ĐÁNH GIÁ HỢP NHẤT, MỤC TIÊU ĐÍCH VÀ PHƯƠNG PHÁP LUẬN GIẢI QUYẾT VẤN ĐỀ

**Ngày lập:** 22/10/2026  
**Trạng thái:** Bản đề xuất tích hợp phương pháp luận và lộ trình có cổng nghiệm thu; **không** phải xác nhận đã triển khai các hạng mục còn thiếu.  
**Workspace đích:** `E:\DEV\Codex-web` (Windows, binding `bind_71661b1046884174b01c99af5f8546aa`).  
**Vị trí khuyến nghị trong repository:** `docs/research/261022_OUTCOME_DRIVEN_INTEGRATED_ASSESSMENT_AND_METHOD.md`.  
**Nguồn chủ đạo:** kiểm toán local/GitHub ngày 22/10; `docs/ROADMAP.md`, `docs/CURRENT_STATE.md`, `docs/ARCHITECTURE.md`, `docs/CODE_EXECUTION_COMPLETION_PLAN.md`, `docs/SINGLE_GOAL_BACKGROUND_CONTINUATION_PLAN.md`, `docs/research/261022_FEATURE_ADOPTION_DECISIONS.md`, `docs/research/261022_FEATURE_EXPANSION_CATALOG.md`; bài Felix Rieseberg *How to be more ambitious: A tutorial for humans with models* (13/10/2026).

> **KẾT LUẬN ĐIỀU HÀNH:** Codex-web đã có nền tảng thực thi, orchestration và evidence tương đối sâu. Nút thắt quyết định hiện nay là chứng minh một luồng liên tục từ **Problem thật → đúng máy/quyền → thực thi → proof → technical acceptance → kết quả người dùng → tri thức tái sử dụng**, chứ không phải bổ sung ngay một kiến trúc agent mới. Nâng tham vọng theo **Altitude** (outcome), **Depth** (dữ liệu/phương pháp/oracle) và **Range** (nhiều lĩnh vực/máy) nhưng chỉ mở rộng quyền tự chủ sau khi có bằng chứng thực nghiệm.

---

## 1. Quy ước nguồn chứng cứ, thời điểm và giới hạn khẳng định

### 1.1. Không đánh đồng các mặt phẳng

Một kết luận phải có nhãn chứng cứ:

1. `DOCUMENTED`: có trong kế hoạch/tài liệu — chưa khẳng định có source.
2. `SOURCE_PRESENT`: mã đã có ở một revision xác định — chưa khẳng định đã chạy.
3. `FOCUSED_PROOF`: unit/service/mock/integration có bản ghi PASS với chính source và môi trường đã quan sát.
4. `TECHNICAL_ACCEPTED`: EOCL/controller đúng quyền đã chấp nhận đúng diff và proof.
5. `ACTIVATED_CURRENT`: thành phần/phiên bản đang chạy khớp revision, activation epoch, workspace, thiết bị.
6. `PACKAGED_RELEASED`: package/installer/delivery hợp lệ — tách riêng với source và activation.
7. `OUTCOME_CONFIRMED`: vấn đề người dùng đã đạt tiêu chí thực tế, với independent outcome receipt phù hợp và cửa sổ theo dõi.

Các trạng thái này là **những chiều chứng cứ tách biệt**, không phải một cờ `DONE`, không suy ra tuần tự một cách tự động. Mọi hồ sơ chứa `source`, `observed_at`, `freshness=live|last_verified|unknown`, `scope`, `fingerprint` và `missing_evidence`.

### 1.2. Snapshot được cung cấp (không nâng thành live authority)

- Báo cáo kiểm toán local: `main@12f3eeeba71db8b9b32de51eb19b30003094280a`, **dirty worktree**; lúc đối chiếu GitHub `main@e58f16743bc988fec07662fdafc2ee38318e973a`. Hai commit local `61d44c89`, `12f3eeeb` không có trong remote snapshot đã khảo sát. Kết luận gắn vào thời điểm kiểm toán, không giả định HEAD vẫn vậy.
- Kiểm thử Work Hub: **74/74 PASS**, sáu file focused Node/service/mock IPC/DOM, không phải native Electron–MCP–user E2E. Python backend chưa chạy trong môi trường audit vì thiếu `pytest`/`PyJWT`; đây là thiếu dependency trong môi trường kiểm toán, chưa phải regression sản phẩm.
- `scripts/dev-ui-lifecycle.js status` lúc kiểm toán: Recovery Host có phản hồi nhưng `DEV_UI_INSTALLATION_MISMATCH`; `fully_ready`, `authority_ready`, `central_connected` chưa xác định. Không kết luận Ubuntu hay package đã tắt.
- Canonical ledger cục bộ tại thời điểm kiểm toán: **42 Problem** (30 provisional, 3 confirmed, 7 open, 2 blocked), **307 sự kiện** (dữ liệu ghi nhận 01–15/09), **3 outcome receipt lưu trong lịch sử**, bảng Goal continuation/observation local có 0 hàng, 1 RUN continuation đã hết hạn tại thời điểm nhìn. Những trường hợp này chưa đủ kiểm chứng causal joins/host-turn/độ phủ cohort; **không lấy 3/42 làm tỷ lệ thành công** và không suy ra chưa từng có khả năng ở môi trường khác.
- Hồ sơ vận hành ngày 13/10 ghi lại: 100 read, 20 patch, 20 readback, 10 Node Job, Git/approved build, 2.078 ms overlap hai workspace. Đây là **bằng chứng lịch sử được đọc qua aggregate**, không phải live proof cho revision hiện tại.
- Kiểm tra qua Ubuntu Control Plane vào tối 22/10: target `DESKTOP-63643J4 – Codex-web` được đăng ký, `online`, binding `active`, `dispatchable`, nhưng `readiness=degraded`, `local_admission=unverified`. Yêu cầu đọc file local đã **queued**, chưa có verified receipt; không nhận diện local HEAD/runtime/owner là live.

### 1.3. Nguồn ưu tiên khi có mâu thuẫn

`Live authoritative runtime/receipt > canonical ledger/EOCL > exact Git/diff/tests > CURRENT_STATE + maintained docs > research/snapshot > hội thoại/suy luận`. Nếu không lấy được nguồn cao hơn, dùng nguồn thấp hơn với nhãn `last_verified` hoặc `unknown`, không giả tạo câu trả lời chắc chắn.

---

## 2. Mục tiêu đích của sản phẩm (North Star)

**Codex-web phải trở thành nền tảng điều phối mục tiêu kỹ thuật đáng tin cậy, sử dụng được từ nhiều thiết bị, thực thi trên đúng máy và workspace được cấp quyền; có khả năng tiếp tục xử lý một Goal trong phạm vi/grant/ngân sách rõ ràng; tự thu thập bằng chứng, phát hiện và xử lý sai lệch có giới hạn; bàn giao kết quả thật; chỉ xác nhận xong khi outcome được kiểm chứng độc lập; học từ nguyên nhân-kết quả lịch sử mà không tự cấp quyền mới.**

Các đích sử dụng:

- Người dùng có thể giao **một Problem với outcome** thay vì lặp hàng chục lệnh sửa bug/test/report.
- Ubuntu giữ vai trò relay/registry/điều phối thường trực; mỗi executor Windows tự quyết định quyền/đường dẫn/lệnh theo local policy. Máy ngủ/tắt **không** thể tự chạy công việc trên máy đó; không tự chuyển sang máy khác.
- Electron Work Hub là bề mặt chọn dự án, chuẩn bị đầu vào, quan sát Job/diff/proof/artifact, điều khiển trong phạm vi cho phép; không thành một hệ quản trị quyền hay source of truth thứ hai.
- Một Coding Tools MCP/EOCL canonical ledger cho từng authority scope; không thêm Goal Engine, controller, execution manager, memory DB hoặc public tool thứ chín nếu không có bằng chứng nhu cầu và quyết định kiến trúc mới.
- `Knowledge` cung cấp case, giả thuyết, dấu hiệu cảnh báo, counterexample và oracle; **không** cấp mutation grant, không auto-accept, không tự quảng bá heuristic thành policy.

### 2.1. Hệ cây mục tiêu và cách lượng hóa

| Cấp | Câu hỏi cần trả lời | Bằng chứng/điều kiện |
|---|---|---|
| North Star | Codex-web có xử lý được vấn đề kỹ thuật dài hạn một cách đáng tin không? | Outcome thật, can thiệp thấp, không sai quyền/đích |
| Outcome / Problem Revision | Người dùng muốn trạng thái thực tế nào thay đổi? | Tiêu chí quan sát được, baseline, owner, time window |
| Goal / bounded episode | Phải đạt điều kiện nào để đóng từng gap? | Có oracle, scope, budget, Stop và state đúng |
| RUN/WAVE / technical | Thay đổi nào được thực hiện trên bytes nào? | Lease, diff, tests, source proof, checkpoint |
| Activation / delivery | Người dùng đang chạy đúng thay đổi chưa? | Runtime identities, installed package/revision, smoke |
| User outcome | Hành vi/lỗi ban đầu thật sự được giải quyết chưa? | Independent receipt, falsification/reopen, follow-up |

Một Goal không phải tập các task được đánh dấu xong; nó là một hợp đồng kết quả có **oracle ngoài model**, chi phí/giới hạn và ranh giới trách nhiệm cụ thể.

---

## 3. Đưa Felix Rieseberg vào phương pháp thực hành, không dùng làm benchmark giả

Bài *How to be more ambitious* định nghĩa bốn chiều: **Speed, Altitude, Depth, Range**. Đây là hướng tư duy từ kinh nghiệm tác giả, không phải một thử nghiệm đã chứng minh ROI cho Codex-web.

| Chiều | Đổi cách làm trong Codex-web | Công cụ/dữ liệu bắt buộc | Oracle |
|---|---|---|---|
| Speed | Giảm thời gian từ yêu cầu đến accepted result, giảm lượt scan/patch/retry | Job/EOCL timings, diff fingerprints, cache/proof reuse, baseline | TTAR, TTPR, cost/rework per accepted result |
| Altitude | Nâng từ “sửa file A” thành “lỗi X không còn tái phát trong luồng thật” | Problem Revision, criterion, RUN/WAVE, grant, continuation | Outcome ngoài model và cửa sổ theo dõi |
| Depth | Đào tới raw crash/log, exact error, call graph, runtime/OS, dữ liệu trước khi kết luận | Reproduction, typed telemetry, test harness, causal hypotheses/falsifiers | Test phân biệt đúng/sai, controlled reproduction, independent check |
| Range | Kết hợp phần mềm, UX, QA, OS, MEP/CAD hay hoạt động sản phẩm khi case đòi hỏi | Adapter đúng môi trường, chuyên gia/protocol, thiết bị thật | Oracle chuyên ngành: CAD objects/BOQ, GUI workflow, business rule |

**Bộ câu hỏi chuẩn trước khi giao AI:**

1. Outcome phía sau task là gì? Nếu task hoàn tất mà outcome vẫn thất bại, người dùng sẽ thấy điều gì?
2. Chuyên gia hàng đầu cần thêm raw data, thiết bị, thử nghiệm hoặc kỹ thuật nào mà task hiện tại chưa yêu cầu?
3. Giả định nào phải bị thử phản chứng? Bằng chứng nào sẽ làm chúng ta thay đổi nguyên nhân gốc?
4. Kỹ năng/ngành nào khác tạo giá trị kiểm chứng thực tế, không chỉ là thêm một vai diễn AI?
5. Đơn vị ngoài model nào quyết định đúng/sai, với nguồn/phiên bản nào?
6. Ai có quyền quyết định thay đổi scope, trả chi phí, deploy, technical accept, xác nhận outcome?

**Không lấy tham vọng làm lý do cho execution vô hạn.** Mục tiêu có thể lớn nhưng mỗi episode phải bounded, fail-closed và kiểm chứng được. Reviewer thứ hai chỉ có giá trị khi mang evidence/harness độc lập; đồng thuận giữa hai model không thay deterministic oracle.

---

## 4. Hiện trạng thực tế: những gì đã có và những gì chưa chứng minh

| Thành phần | Quan sát từ audit/source | Gap phải đóng | Mức chứng cứ |
|---|---|---|---|
| File/Git/context/quick edit | Có service thật, kiểm tra containment, bounded read, expected-hash guarded write | Native GUI E2E; revision/target/dirty attribution đúng | Source + focused proof |
| Recipe → runtime Job | IPC gắn `exec_command`/`command_control`, polling/input/stop | Job/output across reconnect, lost reply, user-visible real run | Source + focused proof |
| Work Hub Queue/Schedule | Queue `Start/Done` đổi local state; lịch thông báo việc đến hạn, người dùng bấm chạy | Không gọi trạng thái local là Job accepted; dispatcher sau nếu thật sự cần | UI preparatory |
| Goal composer | `goalRequestText` tạo text; chưa tự phát grant/chạy nền | Start/consent qua runtime và BG01–BG14 live proof | Preparatory UI |
| Handoff | Có capsule retrieval/revalidation và identity check | Handoff thực có controller, automatic resume được chứng minh | Source + focused proof |
| Continuation backend | Parent/child records, grant, counters, journal, controller fencing và driver tồn tại | Detached next-action, STOP, effect reconciliation, budget consistency qua restart | Source, chưa live-accepted BG toàn bộ |
| Problem/outcome | PRL Revision 4 và runtime-owned receipt mechanism đã có; 3 lịch sử | Độ tin cậy receipt, causal join, natural cohort, false-closure | Source + historical; current unknown |
| Ubuntu + Windows | Registered binding, relay, historical Windows execution | Local admission hiện đang pending; exact activation/install/source parity | Live inventory (degraded) + lịch sử |
| Windows execution safety | Current source default `local/host_user` | Phân biệt host execution với OS isolation; guard unattended write | Source-state, loaded mode unknown |

**Sửa ba hiểu lầm:** (i) chưa chứng minh hôm nay **không** có nghĩa chưa từng thực hiện được; (ii) đã có code backend không có nghĩa luồng sản phẩm đã nghiệm thu; (iii) technical acceptance đúng không có nghĩa outcome đã được xác nhận.

---

## 5. Phương pháp luận vận hành bắt buộc: `PROBLEM → OUTCOME`, 12 bước

Đây là SOP cho mọi Problem đáng kể; áp dụng bằng các primitive hiện hữu, không cần xây state machine hay database song song.

### Bước 0 — Khóa định danh và phạm vi

Xác định rõ machine/device, `binding_id`, `workspace_id/generation`, canonical root, actual HEAD/base, dirty worktree, source/runtime revision, activated package, controller, active writer/lease, RUN/WAVE và jobs. Cấp nhãn `live/last_verified/unknown`. Không tự `reset/clean/merge/restart`; sai installation thì khoanh `SOURCE_RUNTIME_MISMATCH`, dừng nhận định live.

### Bước 1 — Viết hợp đồng Problem Revision

Ghi `symptom`, `user_impact`, `desired_outcome`, `baseline`, `scope`, `protected_invariants`, `acceptance_criteria`, `independent_outcome_oracle`, `falsifier`, `owner`, `time_window`, `risk`, `budget`. Nếu yêu cầu ban đầu chỉ là task, hỏi câu “điều gì thay đổi cho người dùng khi task đó thành công?” để đưa tới outcome nhưng không tự mở rộng phạm vi được phép. Revision chỉ đổi khi hợp đồng người dùng thay đổi, không đổi khi cùng lỗi tái phát.

### Bước 2 — Xây Problem Frame có thể bị phản bác

Mô tả phạm vi tối thiểu `A*`, invariants `G`, hypotheses `H`, trigger/counterexample, evidence gaps. Phân biệt “đã quan sát”, “suy luận”, “giả thuyết”. Shadow frame không cấp quyền. Ưu tiên nguyên nhân có thể phân biệt bằng một phép kiểm tra rẻ thay vì mô tả dài.

### Bước 3 — Thu thập dữ liệu gốc và preflight oracle

Đọc stack/log/diff/test, raw observations của phiên bản đang chạy và semantic context đúng workspace. Tạo reproduction hoặc bằng chứng tương đương trước khi sửa; khi không tái hiện được, báo `UNKNOWN` và chọn probe bổ sung. Đặt oracle trước model patch; tuyệt đối không sửa test chỉ để tạo PASS giả.

### Bước 4 — Đề xuất và chọn chiến lược có điều kiện

Agent có thể xếp hạng hypothesis/next action bằng expected value, giảm rủi ro, blocked dependency, chi phí/latency và proof availability. **Xếp hạng là advisory**, không phải grant. Controller định scope, invariants và quyền thực thi; chọn deterministic tool khi đủ, model chuyên sâu chỉ khi thực sự cần phán đoán; dùng parallel workers khi ownership rời nhau và ROI thực chứng dương.

### Bước 5 — Cấp quyền thực thi bounded

Bind grant với Problem/revision/contract, endpoint/workspace/generation, allowed/protected paths, allowed operations/argv/oracles, budget, expiry, Stop/revoke. Tách `control_owner`, `write_owner + lease`, `acceptance_owner`. Không gán quyền dựa trên máy online hoặc chat được mở. Không tự coi `request_read_only`, read, queue hoặc model text là consent.

### Bước 6 — Chạy EOCL theo source-fenced RUN/WAVE

`PREFLIGHT → READY → ROUTED → EXECUTING → PROVING → ACCEPTING → CHECKPOINTED`. Bất thường: `REPLAN`, `BLOCKED`, `ABORTED`. Một RUN đại diện lineage của một attempt objective; WAVE theo base/worktree/contract/strategy/owner. Không cho writer chồng checkout, không PATCH nếu thiếu lease, không thực thi với source/epoch drift. Dùng preimage và exact hash, giữ failed attempts.

### Bước 7 — Kiểm chứng bằng trọng tài ngoài model

Chạy proof nhỏ nhất phân biệt lỗi gốc, sau đó kiểm tra phạm vi ảnh hưởng và một adjacent credible risk. Mọi test/reproduction phải bind `source/config/toolchain/oracle/fingerprint/proof ID`. `exit_code=0` chỉ là trạng thái process, không tự suy ra test count hay outcome. Nếu UNKNOWN, yêu cầu evidence/reconcile; không tự PASS. Chỉ reuse proof khi fingerprint y hệt.

### Bước 8 — Replan có nguyên nhân và chính sách không lặp

Nếu FAIL, ghi nguyên nhân phân loại (`BASE_DRIFT`, `PATCH_AMBIGUOUS`, `DEADLINE`, `CAPACITY`, `PROOF_TIMEOUT`, `CONTRACT_DRIFT`, `SUPERVISOR_NOT_READY`, v.v.). Mọi lần retry phải có evidence/strategy/scope thay đổi đáng kể; không thử lại y nguyên vô hạn. Lost ACK/unknown effect phải reconcile receipt/actual effect trước khi dispatch mutation mới.

### Bước 9 — Continuation sau lượt chat (khi đã có grant hợp lệ)

Đặt intent/action identity trước dispatch. Quan sát `turn/completed` và oracle; FAIL recoverable → typed next proposal → validate → next actual turn/job; PASS → review boundary; UNKNOWN → bounded evidence hoặc block. Chat response kết thúc không đồng nghĩa dừng worker đã được cấp quyền; STOP/revoke/expiry phải thắng race. Parent budget và reservations không reset qua child/restart. Không đánh thức trang ChatGPT bằng DOM/browser typing để giả tự chủ.

### Bước 10 — Hai vòng nghiệm thu riêng

**Technical:** controller kiểm tra diff, proof, invariants, source và đúng quyền; chấp nhận/checkpoint hoặc reject → replan. **Outcome:** triển khai đúng bản, chạy workflow thật, dùng oracle/nguồn độc lập của người dùng và `confirm` receipt có authority; nếu không có, `WAITING_USER_OUTCOME/PROVISIONAL`; nếu lỗi còn, `reopen same revision`. Không tự đóng Problem khi chỉ có model report hoặc unit test xanh.

### Bước 11 — Cập nhật tri thức có phản chứng và đánh giá kinh tế

Ghi symptom → trigger → hypothesis/falsifier → test distinguishing cause → fix → proof → user outcome/reopen → recurring risk/early warning. Giữ raw source ID/hash, loại bỏ dữ liệu nhạy cảm. Tri thức lịch sử chỉ giúp định vị/đề xuất, phải revalidate ở HEAD/environment mới; không cấp write/acceptance authority. Đo tổng thời gian và chi phí từ start tới outcome, bao gồm rework/failures và human relay được quan sát thật.

---

## 6. Hợp đồng dữ liệu và cấp quyền (không xây nguồn sự thật thứ hai)

**Causal lineage tối thiểu:**

`Problem ID + Revision + Contract FP → Goal Episode/Parent Grant → RUN/WAVE → Child Action/Job/Effect → Source/Proof FP → Technical Checkpoint → Runtime/Artifact → Independent User Outcome/REOPEN`.

Phân loại nguồn:

- **Authority:** ledger/runtime EOCL, consent grant, writer lease, controller accept, runtime-owned independent outcome receipt.
- **Evidence:** Git, file hash/preimage, reproducible test, Job exit+stdout/retention, artifact hash, activation epoch, source-bound observations.
- **Projection:** Work Hub cards, queue list, `performance.json`, dashboard/report; không ghi đè state canonical.
- **Advisory:** AI hypotheses, priority score, retrieved knowledge, UI patch marker, self-reported `done`.

**Atomic budget:** `consumed + reserved + available = authorized_total`. Child không được cấp vượt parent remainder; unknown effect giữ reservation; expiry tuyệt đối không reset qua reboot; STOP/revoke ưu tiên tuyệt đối. Con số `60 phút/4 episode/32 turn/8 patch` trong kế hoạch September là **mức đề xuất**, không tự coi đã triển khai. Source audit cho thấy RUN-like bound `900 giây/12 turn/3 patch` hiện hữu; bắt đầu với bounded contract đã có và chỉ tăng sau proof.

**Transport vs trust:** Ubuntu gateway chuyển yêu cầu và giám sát, không tự cấp phép vào Windows; control plane inventory/online không cấp OS quyền. Windows local host-user execution chỉ có admission ứng dụng, **không** là sandbox; unattended mutation phải có rào cản đúng mode và local policy. Offline node không tự có process hoặc quyền để thực hiện.

**Tính riêng tư:** ưu tiên opaque IDs, bounded status, hashes, time/clock provenance, causal links; không lưu raw credentials, transcript hay private reasoning trong telemetry.

---

## 7. Phân tích nguyên nhân của các gap đã thấy và phương án kỹ thuật

| ID | Gap / biểu hiện | Nguyên nhân/hợp đồng chưa khép kín | Phương án tối thiểu | Oracle/nghiệm thu |
|---|---|---|---|---|
| G01 | Development UI báo `DEV_UI_INSTALLATION_MISMATCH` | Checkout và Recovery Host khác installation; loaded version unknown | Read-only identify installed candidate/host/epoch/source; quyết định activation riêng, không restart để đoán | Bản đang dùng, thư mục và component hashes/epoch khớp hoặc BLOCKED có lý do |
| G02 | Ubuntu online nhưng `degraded`, local read queued | Registry/relay != verified node admission; request thiếu receipt | Trace action state, local policy/admission/worker trên node theo quyền hợp lệ; không khẳng định đã read | Một canary read từ đúng binding trả verified receipt và exact content provenance |
| G03 | Queue `Done` và feedback `acknowledged` do UI đặt | Projection local dễ giả kết quả hệ thống | Đổi nhãn `Nháp/Đã chuẩn bị/Đã gửi/Đã nhận/Đã chạy/Đã kiểm chứng/Chờ duyệt/Xác nhận outcome`; nhận ACK từ runtime, không cho người dùng tự tạo controller receipt | Không thể nhìn queue manual `done` thành runtime PASS; stale/duplicate events không lẫn |
| G04 | Patch UI approval chỉ key bằng relative path | Thiếu namespace workspace/identity | Scope visual approval bởi workspace ID/generation + task/run + source/base + diff digest; expiry/invalidation rõ; runtime consent vẫn tách riêng | Hai workspace cùng path/diff không dùng chung mark; đổi source mất hiệu lực; test negative |
| G05 | Job ID bền, output có `restart_safe=false` | Artifact output thuộc process_runtime | Giữ đủ receipt/output cần thiết bằng artifact bounded/hash đúng owner hoặc báo rõ unavailable sau restart | Reconnect/restart: biết output có hay không, không suy tạo hoặc chạy lại |
| G06 | Goal composer không tự dispatch | `goalRequestText` là chuẩn bị văn bản, chưa grant/Start | Nối một supported client với runtime Start có receipt; không dùng browser chat injection | Một hợp lệ Start duy nhất có durable ID; double click/idempotency không tạo duplicate |
| G07 | Background Goal chưa hoàn tất proof BG01–BG14 | Parent/driver/counters có nhưng chưa proven đủ live/causal | Tái dùng modules hiện có; chứng minh detached real dispatch và fault matrix | Real next action, STOP, budget, no duplicate, controller boundary đạt |
| G08 | Build/test đường phụ và Job có thể khác lifecycle | Job memory/manual build service chưa cùng provenance | Bọc/nối từng use case vào existing Job receipt; không xây process manager thứ hai | Recipe/test/build hiển thị đúng cùng Job/run/artifact và trạng thái output |
| G09 | Outcome có receipt lịch sử nhưng cohort thiếu | Dữ liệu local cũ, causal join chưa audit, host-turn chưa xác minh | Reconstruct exact lineage theo revision/event+receipt, natural cases prospectively | Case có source→proof→checkpoint→outcome hoặc rõ unknown/blocked |
| G10 | Remote source/local worktree/packaged candidate khác nhau | Drift đồng thời và snapshot nhiều thời điểm | State capsule, owner lease, explicit integration delta; giữ dirty changes và không tự push | Không proof reuse sai fingerprint, không source cũ bị gán cho bản mới |
| G11 | Windows host-user default | Execution admission không là OS isolation | Hiển thị rõ effective mode; opt-in/local scope và deny destructive commands; sandbox khi bảo đảm isolation cần thiết | Unauthorized argv/path bị deny trước spawn; kiểm chứng token/capability theo mode |
| G12 | Multi-workspace + reviewer/worker scale | Có target và lanes nhưng chưa chứng minh coordination toàn bộ | Chỉ mở multi-writer với separate worktree/lease; no implicit failover; reviewer read-only | Không shared checkout writers; không target switch làm thay đổi Job cũ |

**Không được sửa sai loại:** G04 là defect của *UI advisory state*, không phải bằng chứng đã bypass quyền runtime. G02/G01 là blocker xác minh live, không đủ chứng minh nguồn code lỗi. G05 là hạn mức hợp đồng retention, chưa đồng nghĩa dữ liệu đã mất. G07 là khoảng trống kiểm chứng end-to-end, không phải “chưa tồn tại backend”.

---

## 8. Mức ưu tiên tích hợp A1–A8 và 40 ứng viên tính năng

**Chức năng không phải mục đích tự thân.** Chỉ đưa vào M1 những gì làm được luồng end-to-end thực tế:

| Nhóm | Quyết định | Nghiệm thu sản phẩm |
|---|---|---|
| A1 File/context | KEEP/MODIFY: dùng viewer/service hiện có, content có version/ref, workspace/generation fencing | Chọn đúng file/đoạn, khi đổi dự án không nhận stale reply |
| A2 Diff/Git | MODIFY: task-scoped attribution, exact base/current, rename/untracked, guarded patch | Diff đúng Job/HEAD; không gán toàn dirty tree cho AI |
| A3 Job/recipe | KEEP/MODIFY: current IPC thật; hoàn thiện receipt, retention, reconnect, control | Run/observe/stop đúng 1 Job, không replay lost response |
| A4 Artifact/report | MODIFY: source-bound hash, mở/tải/preview với owner đúng | Người dùng lấy được sản phẩm của đúng RUN hoặc thấy unknown |
| A5 Draft/search | KEEP, tinh gọn sau M1 | Giảm thao tác nhưng không tự chạy từ nháp |
| A6 Notification | MODIFY: canonical event, dedup, click đúng Job, keep-awake scoped | Thông báo có hành động, không giữ máy thức sai |
| A7 Task/worker board | CONDITIONAL sau scoped detail + authority | Nhiều task/worker khác scope không trộn trạng thái/Stop |
| A8 Handoff/continuity | KEEP/MODIFY: canonical capsule, revalidation, legitimate control handoff | Không chạy lại lệnh; không gán tiếp tục text là dispatch thực |

**Các ứng viên F15 queue, F23 Goal, F24 scheduler, F27 worktree, F33 machine picker, F34 Skills, F37 browser QA, F38 Windows GUI automation, F40 SSH** chỉ mở theo use case/điểm nghẽn. Phải ghi `KEEP/MODIFY/DEFER/REMOVE` đối với từng mục trong 40-item catalog sau pilot; catalog là backlog nghiên cứu, không là cam kết feature-complete.

Đừng nhập nguyên khối từ Chat On Steroids/WebCodex: giữ trải nghiệm hữu ích và contract đã học, **không** thêm chat DOM recorder, universal plugin gateway, Goal/Memory DB hoặc nhiều public MCP tools chỉ vì nguồn tham khảo có.

---

## 9. Lộ trình triển khai M0–M5 với cổng dừng, owner và bằng chứng

### M0 — Chốt source/runtime/authority và đo baseline (**ưu tiên số 1**)

**Owner:** controller + operator thiết bị; chỉ đọc tới khi xác định đúng đích.  
**Làm:** chọn binding Codex-web; xác minh lại local admission và read receipt; lấy workspace root/source HEAD+dirty manifest, current installed package/epoch, EOCL owner/lease/active jobs, build/test harness; phân loại mismatched docs/current; chốt một Problem/revision/oracle; bật instrumentation từ đầu.  
**Exit:** ít nhất một read-only canary verified đúng máy/thư mục; đã xác định hoặc ghi typed blocker của mọi identity quan trọng; không động tới writer hiện hữu.  
**STOP:** admission không xác minh hoặc source/installation drift chưa được reconciled. Không ép restart/clear/reinstall để tạo readiness xanh.

### M1 — Khép kín một luồng Work Hub → runtime → proof → review

**Owner:** UI/IPC integration owner và runtime owner, mỗi mutation một write lease.  
**Làm:** chốt supported submission channel với durably acknowledged task ID; sửa G03/G04; nối context, Job, diff, test, artifact và review. Sửa những lỗi thật ảnh hưởng luồng chứ không rebuild toàn Hub.  
**Exit:** native Electron thực hiện *chọn đúng dự án/file → submit một lần → quan sát Job → review diff → focused test → lấy artifact → technical acceptance chờ/đã nhận đúng quyền*; bài negative switch project, stale reply, lost ACK, double click, concurrent change đều không gây false attribution.  
**STOP:** UI chỉ preview, chưa có durable task receipt; không gọi full end-to-end PASS từ mock.

### M2 — Một Goal chạy nền bounded, không manual relay thừa

**Owner:** continuation writer + controller acceptance; dùng `SINGLE_GOAL_BACKGROUND_CONTINUATION_PLAN.md` B0–B7.  
**Làm:** Start/consent thật; validate grant/source/expiry; reuse continuation driver, parent/child ledger, `codex_bridge`, effect journal, EOS/Stop; chứng minh provider turn tiếp theo. Dùng mức 900s/12 turns/3 patch attempts khi đó là contract đã được runtime hỗ trợ, nâng parent budget đề xuất chỉ sau test atomic reservation + controlled permission.  
**Exit:** response chat ban đầu kết thúc nhưng một FAIL recoverable sinh next action thật; duplicate/lost response không mutation lặp; STOP/revoke/expiry thắng; budget không reset; reviewer vẫn đúng controller; chưa có outcome receipt thì PROVISIONAL.  
**STOP:** UNKNOWN effect, reviewer unavailable, no oracle, no progress, hết budget, invalid grant hoặc policy drift phải block có lý do chứ không lặp vô hạn.

### M3 — Một Problem tự nhiên và tập 5–10 case để đánh giá

**Owner:** controller + domain operator/evaluator độc lập.  
**Làm:** chọn Problem thật có ảnh hưởng người dùng, trace từ intake đến kết quả; lỗi patch cross-workspace chỉ dùng natural pilot nếu có tình huống dùng thật, còn reproduction giả lập là fault canary riêng. Sau đó thu 5–10 case khác biệt lớp bug/tính năng/môi trường.  
**Exit:** case reconstructable, cả các lần FAIL/replan/unknown/reopen; tài liệu hoá intervention, source/proof/artifact/activation; có outcome receipt hoặc thiếu rõ ràng. Không gán success từ 74/74 tests hay 3 lịch sử receipt.

### M4 — Chuẩn hóa tri thức và so sánh hiệu quả

**Owner:** product/engineering analyst, sử dụng projection/report từ canonical ledger.  
**Làm:** outcome evaluation, recurrence, no-progress, rework, time/cost; kiểm tra coverage và missingness; case-based retrieval với counterexample; thử control/treatment giữ nguyên task class/model/route/oracle khi có đủ mẫu.  
**Exit:** có báo cáo KEEP/MODIFY/REMOVE từng cơ chế, không promo heuristic thành auto policy nếu chưa có cohort/replication phù hợp.  
**STOP:** sample quá nhỏ hoặc logging lệch không thể kết luận ROI/causal.

### M5 — Mở rộng nhiều máy, Goal và chuyên ngành có điều kiện

**Owner:** product owner + security/runtime owner.  
**Làm:** target picker, queued offline visibility, optional scheduling, worker/worktree khi tách được quyền, CAD/browser adapters cho case cụ thể. Chỉ khi M1–M4 chỉ ra bottleneck.  
**Exit:** giảm đáng kể accepted-result friction hoặc tăng verified outcome dưới chất lượng/bảo mật không đổi; không duplicate writers, quyền không tự retarget, offline không tự failover.  
**STOP:** thêm complexity lớn hơn giá trị đo được.

### Phụ thuộc trọng yếu

`M0 → M1 → M2 → M3 → M4 → M5`. Khảo sát/chứng cứ read-only ở M3 có thể bắt đầu cùng M1; tuyệt đối không dùng research tiến độ thay cho thực thi/cấp quyền. Không mở thêm một `Problem` mới chỉ để đổi tên một vấn đề vẫn còn cùng hợp đồng; reuse/revise đúng Revision lineage.

---

## 10. Bộ oracle BG01–BG14: không thiếu một điều kiện cốt lõi

| Cổng | Điều cần chứng minh trong M2–M3 |
|---|---|
| BG01 | Exact Problem Revision/endpoint/workspace/owner; Start idempotent, no duplicate |
| BG02 | Chat response end không hủy grant đã cho phép; Stop/revoke dừng |
| BG03 | PASS/FAIL/UNKNOWN từ oracle thật, không từ lời model |
| BG04 | FAIL recoverable tạo typed proposal và actual next dispatch/observe |
| BG05 | Parent/child budget atomically reserved/consumed, restart không reset |
| BG06 | Duplicate/out-of-order/lost response/unknown effect không lặp mutation |
| BG07 | Reconnect/replacement kiểm tra exact source/epoch/authority và đúng máy |
| BG08 | Expiry/no-progress/revoked/blocked dừng hữu hạn có typed reason |
| BG09 | Reviewer đúng controller; ACCEPTING không auto-accept |
| BG10 | Natural pilot không unnecessary manual nudge/relay, có observation source |
| BG11 | Problem/revision → RUN/WAVE → action → proof → outcome causal lineage đủ |
| BG12 | Telemetry idempotent, riêng tư, coverage rõ; synthetic tách natural |
| BG13 | Source/proof/runtime/activation exact và rollback giữ lịch sử |
| BG14 | Outcome chỉ confirmed bởi user-authority independent receipt; không đúng thì reopen |

**Lưu ý:** PASS v1 có thể dừng hợp lệ ở `WAITING_REVIEW` hoặc `WAITING_USER_OUTCOME`, không được giả “full Problem CLOSED”. Approval hợp lệ là human decision đúng trách nhiệm, không được đếm là manual nudge thừa.

---

## 11. Thiết kế pilot thật và fault injection tách biệt

**Pilot tự nhiên số 1:** một lỗi đang thực sự cản sử dụng Work Hub/Codex-web; mô tả hành vi sai được operator nhìn thấy, không tự tạo bug chỉ để kiểm thử.  
**Ứng viên đã có reproduction kỹ thuật:** dấu duyệt patch ở UI chỉ key `relative path`, thiếu workspace; nếu có một use case thật của người dùng mới tính natural. Không coi bug UI là privilege escalation nếu không có oracle chứng minh vượt quyền runtime.

**Chuỗi quan sát chuẩn:**

1. Ghi symptom + exact app/version + test dùng được để tái hiện + owner outcome.
2. Chốt Problem/revision, workspace/root/generation, oracle, budget, Stop và no-out-of-scope paths.
3. Có durable task/grant receipt, không lặp Start.
4. Worker thực hiện scoped patch, log diff SHA/Job identity; test phân biệt behavior có lỗi và sau sửa; không đụng unrelated dirty files.
5. Kết thúc initiating ChatWeb response; quan sát một next action thật theo grant (không human relay).
6. Đánh giá independently diff/test/artifact và loaded target (nếu triển khai); controller technical accept đúng quyền.
7. Người dùng thử hành vi trước kia sai; ghi user outcome receipt hoặc reopen same revision. Ghi thời gian/can thiệp/chi phí và knowledge case.

**Fault canary tách khỏi outcome:** double-click/start, stale source, wrong workspace, same-relative-path, process crash, timeout, lost ACK, duplicate event, revoked/expired grant, pending effect during restart, Stop race, offline executor, denied command và package mismatch. Cần negative assertions; không ghi canary là resolved natural problem.

---

## 12. Hệ KPI: chỉ đo trách nhiệm gánh được, không đếm tool call làm thành tựu

| Metric | Công thức/định nghĩa bắt buộc | Chú ý |
|---|---|---|
| Verified Outcome Rate (VOR) | `N exact eligible Problem Revisions confirmed with valid independent outcome / N eligible Revisions started in fixed cohort window` | Báo riêng pending/blocked/missing; không dùng `3/42` |
| Time to Verified Outcome (TTVO) | `confirmed_at - goal_authorized_start` với window và censored/pending được công bố | Technical accepted time báo riêng |
| Time to Technical Acceptance (TTAR) | `accepted_checkpoint_at - execution_start` trên declared cohort | Bao gồm thất bại/retry; không chỉ lấy success |
| Manual relay / unnecessary nudge | Số lần operator thật phải copy report/retype “tiếp tục” trong cửa sổ hợp lệ | Approval mới/chỉnh scope/acceptance không là unnecessary nudge |
| False closure & recurrence | Số case reopen tương ứng / số case eligible theo dõi đủ cửa sổ | Phân biệt bug cũ, regression, requirement mới |
| Evidence coverage | `N criterion có proof/source/oracle/provenance hợp lệ / N criterion yêu cầu` | Unknown denominator công bố riêng |
| Duplication / wrong-target | `duplicate mutations prevented`, `wrong-target executions`, `write without lease` | Wrong-target/unauthorized write target là 0 |
| Cost per accepted outcome | Model + tools/test + rework + operator time, chỉ cộng phần quan sát được | Internal credits không được gọi provider billing |
| Quality of knowledge | Số case tái sử dụng giúp giải quyết đúng / số case retrieval eligible có follow-up | Retrieval similarity không là causal proof |

**Cửa sổ mẫu:** một natural pilot rồi cohort 5–10 case để hiệu chỉnh measurement/feasibility, chưa đủ chứng minh causal ROI. Muốn thay route/policy phải có prospective/paired benchmark với quality floor, model/route/compute/oracle và task class tương đương. Missing instrumentation là `unknown`, không điền 0. Dữ liệu synthetic và natural phải phân tầng rõ.

---

## 13. Cơ chế tri thức và học hỏi không biến heuristic thành authority

Mỗi case có cấu trúc:

```yaml
case_id: <runtime-issued-or-report-id>
problem_revision: <exact-id+revision>
source_scope: <workspace+HEAD+worktree-fingerprint>
symptom: <observed>
trigger: <verified-conditions>
hypotheses:
  - claim: <candidate-cause>
    discriminator: <test-or-observation>
    evidence_status: observed|refuted|unknown
root_cause: <confirmed-or-unknown>
change_ref: <patch-identity-and-paths>
proof_refs: [<source-bound-proof-ids>]
technical_acceptance: <accepted|rejected|pending>
activation: <current|historical|unknown>
user_outcome: <confirmed|reopened|pending|unknown>
recurrence_window: <start-end-or-unobserved>
lessons:
  - <portable-hypothesis-with-guardrails>
authority_note: advisory_only
```

Quy trình tái sử dụng: retrieve **case có source**, đối chiếu điều kiện hiện tại với trigger và counterexample, chạy oracle mới, mới đề xuất action. Không copy blindly patch của case cũ. Không log private reasoning hoặc secrets. Không tạo memory engine thứ hai; dùng canonical IDs, bounded report/projection và search adapter sau khi có use case.

Hệ thống có thể đề xuất `priority_score` để người dùng chọn Goal theo giá trị, mức độ khẩn cấp, risk, dependency, context readiness, proof readiness, cost. **Không được tự cấp quyền Goal mới theo score;** explicit grant hoặc policy đã nghiệm thu mới quyết định dispatch.

---

## 14. Cách đưa phương pháp luận vào repository mà không phá các nguồn hiện có

Không thay thế các tài liệu gốc bằng bản tổng hợp này và không viết lại lịch sử research để tạo cảm giác đã hoàn thiện:

1. **Tài liệu độc lập:** đặt nội dung này ở `docs/research/261022_OUTCOME_DRIVEN_INTEGRATED_ASSESSMENT_AND_METHOD.md` dưới nhãn `DESIGN/PLAN; NOT ACCEPTANCE`.
2. **`docs/ROADMAP.md`:** sau khi xác minh source và quyền sửa, thêm một liên kết tới tài liệu này ở phần convergence; giữ nguyên nguyên tắc **“Do not build more system”** và `KEEP/MODIFY/REMOVE` trên evidence.
3. **`docs/CODE_EXECUTION_COMPLETION_PLAN.md`:** liên kết M0–M1, proof/acceptance/source→running exact, không làm giả release gate.
4. **`docs/SINGLE_GOAL_BACKGROUND_CONTINUATION_PLAN.md`:** liên kết M2/BG01–BG14 và phần budget; giữ B0–B7 và ownership, không claim full BG đã PASS.
5. **`docs/research/261022_FEATURE_ADOPTION_DECISIONS.md`:** dùng matrix A1–A8/Fxx để ưu tiên; không ghi 40 features là đã triển khai đầy đủ.
6. **`docs/ARCHITECTURE.md`:** chỉ điều chỉnh khi implementation/authority contract thực tế đã thay đổi, không thêm một brain hoặc controller song song.
7. **`.coding-tools`:** bảo toàn canonical ledger, task/history/performance/reports; mọi ghi event qua producer hợp lệ, không direct-edit DB/log nhằm cải thiện số liệu. Nếu commit/push, tuân thủ `npm run stage:coding-tools-delivery` rồi `npm run check:coding-tools-delivery` và explicit delivery authorization.

**Không tự thực hiện:** restart, redeploy, commit, push, release, activate, mở grant dài hạn, chạy paid model, chỉnh policy hoặc ghi canonical ledger từ tài liệu này.

---

## 15. Definition of Done (DoD) cho mục tiêu dự án, không phải phần trăm tùy ý

Mục tiêu Codex-web chỉ gọi **đạt vận hành ở phạm vi được nghiệm thu** khi:

- [ ] Có exact live workspace/source/runtime identity + authorized read receipt; không còn UNKNOWN chưa khai báo ở đường chính.
- [ ] Một native Electron E2E chạy từ request→Job→diff→proof→artifact→review trên đúng target, có negative guards.
- [ ] Goal được cấp quyền có thể tiếp tục sau initiating response, sinh actual next dispatch; Stop/revoke/expiry, budget và dedup chứng minh qua fault matrix.
- [ ] Controller technical accept/reject và independent user outcome là hai cổng riêng, có honest `provisional/reopen`.
- [ ] Ít nhất một natural Problem end-to-end có complete causal lineage; cohort 5–10 case có cả thất bại/không đủ dữ liệu và denominator rõ.
- [ ] Các failure modes sai đích, sai quyền, writer trùng, proof reuse sai FP, tự nhận success bị chặn bằng oracle thực.
- [ ] Có quyết định Keep/Modify/Remove định kỳ từ measured accepted-result economics, không áp dụng heuristic/policy tự động khi chưa chứng minh.
- [ ] Phạm vi Ubuntu 24/24 và thiết bị Windows được báo cáo đúng: control plane luôn quan sát/điều phối trong khả năng, executor offline không thể thực thi và không có failover ngầm.

**Ngay trước khi bắt đầu sửa:** M0 phải phân biệt `head trên GitHub`, `head+dirty local`, `runtime-loaded source` và `installer đang dùng`. Với kiểm tra đã có, chỉ khẳng định local audit + online/degraded binding; chưa được coi M0 PASS.

### Chốt hành động ưu tiên

**Ưu tiên cao nhất:** xử lý M0 (chỉ đọc, exact identity và local admission), đồng thời lập một Problem natural có oracle quan sát được. Sau đó sửa nhỏ để đóng M1, rồi chứng minh M2 qua một episode bounded. Đây là con đường ngắn nhất để đạt *một kết quả thật, có proof và không phải nhắn “tiếp tục” thừa*, trước khi mở rộng thêm hệ thống.

---

## 16. Tài liệu tham chiếu

- Felix Rieseberg, [How to be more ambitious: A tutorial for humans with models](https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/), 13/10/2026.
- Codex-web: [ROADMAP](https://github.com/uyenthudao2410-code/Codex-web/blob/main/docs/ROADMAP.md), [CURRENT_STATE](https://github.com/uyenthudao2410-code/Codex-web/blob/main/docs/CURRENT_STATE.md), [ARCHITECTURE](https://github.com/uyenthudao2410-code/Codex-web/blob/main/docs/ARCHITECTURE.md), [CODE_EXECUTION_COMPLETION_PLAN](https://github.com/uyenthudao2410-code/Codex-web/blob/main/docs/CODE_EXECUTION_COMPLETION_PLAN.md), [SINGLE_GOAL_BACKGROUND_CONTINUATION_PLAN](https://github.com/uyenthudao2410-code/Codex-web/blob/main/docs/SINGLE_GOAL_BACKGROUND_CONTINUATION_PLAN.md).
- Codex-web: [Feature Adoption Decisions](https://github.com/uyenthudao2410-code/Codex-web/blob/main/docs/research/261022_FEATURE_ADOPTION_DECISIONS.md), [40-item Feature Expansion Catalog](https://github.com/uyenthudao2410-code/Codex-web/blob/main/docs/research/261022_FEATURE_EXPANSION_CATALOG.md).
- Người dùng cung cấp: `codex-web-audit-2026-10-22.json` (snapshot source, focused tests, ledger, history, blockers), `codex-web-assessment-2026-10-22.html` (đánh giá phân tầng), `Văn bản đã dán...txt` (diễn giải tiếng Việt).

**Trạng thái tài liệu:** tư vấn phương pháp luận đã hợp nhất; code/runtime/Ubuntu admission/live Problem acceptance phải được kiểm chứng và triển khai theo các cổng nêu trên. Không ghi tên một bước kế hoạch thành sự kiện đã hoàn tất.
