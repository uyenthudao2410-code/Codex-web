# Kế hoạch đóng Durable RUN Continuation — bàn giao cho AI thực hiện

Ngày lập: **08/09/2026**, múi giờ Việt Nam. Workspace: `E:\DEV\Codex-web`.

**Đây là kế hoạch, không phải biên bản PASS hay lệnh tự động cấp quyền.** Việc lập tài liệu không khởi động provider, tạo RUN/Problem, cấp consent, sửa sản phẩm, restart, commit/push hoặc phát hành. AI được giao triển khai phải đối chiếu quyền của yêu cầu mới với từng bước dưới đây.

## 0. H0 — Mở đúng authority path ChatWeb trước G0

**Trạng thái hiện hành sau đợt 16:36 +07: H0 đã sửa source, có local behavioral proof, exact-byte adoption, controller acceptance và report ACK; không làm lại packet đã đóng bên dưới.** Còn activation bị preflight từ chối `ACCEPTANCE_PENDING` do một RUN Control Center khác. Các mô tả nguyên nhân và bước sửa H0 dưới đây ghi lại baseline trước patch để giải thích giải pháp, không phải lệnh sửa lại. Không chữa authority bằng reconnect thêm, tạo receipt giả, raw HTTP/copy `hub_client`, hay tái dùng receipt Electron cũ.

Lần thử public `task_control(action="problem", problem_event.operation="open")` từ Coding-VP Live đã fail-closed với `PRL_HOST_IDENTITY_UNAVAILABLE`: runtime đòi một `electron_pending_host_turn` one-shot. File `.coding-tools/evaluation/chatweb-host-turn-pending.json` hiện không có và entry deleted trong worktree là receipt lịch sử/đã hết hạn; tuyệt đối không restore, sửa hay tạo lại file đó.

Tại baseline trước patch, `workflow_tools.py::_attested_chatweb_transport_turn()` đã cung cấp authority path cho loại client này: chỉ trả identity khi managed transport xác nhận đồng thời `client_type=chatweb`, `role=controller`, `identity_source=attested_transport`, `attestation_verified=true`, và request có trace ID hợp lệ theo helper hiện hành. Hàm tự derive `turn_id=chatweb-trace:<trace_id>`; caller không cung cấp được identity này. `agent_workflow` đã dùng fallback đó khi không có Electron receipt, nhưng `problem_lineage_control.py::_problem_claim_host_identity()` trước H0 chỉ gọi `claim_pending_host_turn()`. Vì continuation grant cần exact Problem Revision binding, asymmetry này chặn external attested ChatWeb đi từ Problem sang grant. H0 đã nối lại fallback tại đúng nhánh này; live behavior vẫn cần loaded-source proof riêng.

### H0.1 — Packet source nhỏ nhất

**Ownership/scope:** chỉ `resources/coding-tools-mcp/coding_tools_mcp/problem_lineage_control.py` và `resources/coding-tools-mcp/tests/test_problem_lineage.py`. Không chạm `.coding-tools`, `workflow_tools.py`, bridge/provider configuration, public schema, continuation budget, route, sandbox hay Electron receipt protocol trong packet này.

**Thay đổi cần làm trong `_problem_claim_host_identity(event)`:**

1. Giữ `claim_pending_host_turn(workspace, process_instance_id=...)` là đường ưu tiên và giữ nguyên atomic claim/consume/restore với Electron receipt.
2. Chỉ khi claim trả `None`, gọi helper sẵn có `self._attested_chatweb_transport_turn()`.
3. Nếu helper trả identity, dùng nguyên `turn_id`/`trace_id` runtime-derived đó để bind event; không tạo pending file và không convert transport identity thành Electron receipt.
4. Với cả hai nhánh, nếu event có `turn_id` hoặc `trace_id` supplied và không khớp exact derived identity thì trả `PRL_HOST_IDENTITY_MISMATCH` như hiện tại. Không tin giá trị caller để thay authority.
5. Nếu cả Electron claim và attested transport đều không tồn tại, giữ nguyên exact failure `PRL_HOST_IDENTITY_UNAVAILABLE`.
6. `restore_pending_host_turn(...)` và `consume_pending_host_turn(...)` phải tiếp tục là no-op an toàn cho dictionary transport không có claim path; không thêm persistence side effect.

Pseudo-code để AI định vị logic, **không phải patch được copy mù**:

```python
claimed = claim_pending_host_turn(...)
authoritative = claimed or self._attested_chatweb_transport_turn()
if authoritative is None:
    raise ToolFailure("PRL_HOST_IDENTITY_UNAVAILABLE", ...)
if supplied_identity_conflicts(event, authoritative):
    if claimed:
        restore_pending_host_turn(...)
    raise ToolFailure("PRL_HOST_IDENTITY_MISMATCH", ...)
event["turn_id"] = authoritative["turn_id"]
event["trace_id"] = authoritative["trace_id"]
return authoritative
```

**Regression bắt buộc:** trong isolated temporary `Runtime`, activate PRL schema; attach current attested `chatweb/controller` identity và `request_context.trace_context={"trace_id": "a" * 32}`; không stage pending receipt; gọi public `runtime.task_control()` với `action="problem"` và public `open` event. Assert exact Problem Revision 1 được tạo, event dùng `turn_id="chatweb-trace:" + trace_id`, `trace_id` đúng, provenance runtime-derived đúng policy hiện hành, và không có pending receipt được tạo. Giữ/thêm negative test: thiếu attestation hoặc trace vẫn trả `PRL_HOST_IDENTITY_UNAVAILABLE`.

**Proof tối thiểu sau patch** (chạy từ `E:\DEV\Codex-web\resources\coding-tools-mcp`; thay `<NEW_TEST>` bằng node ID thực tế sau khi tạo):

```powershell
python -m pytest tests/test_problem_lineage.py::ProblemLineageTests::<NEW_TEST> -q
python -m pytest tests/test_problem_lineage.py::ProblemLineageTests::test_runtime_autofills_host_identity_and_pins_declared_revision_before_run -q
python -m pytest tests/test_problem_lineage.py -q
python scripts/check_module_size.py
git -C E:\DEV\Codex-web diff --check -- `
  resources/coding-tools-mcp/coding_tools_mcp/problem_lineage_control.py `
  resources/coding-tools-mcp/tests/test_problem_lineage.py
```

**PASS H0-source:** focused public-path regression và existing Electron path pass; diff chỉ thuộc two-path scope; no receipt/source evidence was fabricated. **Không phải PASS G1–G5:** source/test pass không chứng minh MCP đang load bản mới, live provider, detached autonomy hay natural outcome.

### H0.2 — Activation và thử lại live, sau khi source proof đạt

1. Review exact diff and lease/owner state. Do not merge unrelated dirty WIP.
2. Trước activation, đóng provenance/nghiệm thu đúng hai file H0 qua packet kỹ thuật no-patch của runtime. Không giả một natural Problem để bootstrap PRL đang lỗi; technical acceptance không cấp continuation grant và không đóng G5. `work_origin=non_problem` chỉ được dùng cho công việc ghi nhận provenance riêng này, không dùng để phủ nhận hay đóng Problem gốc. Không dùng checkpoint recovery cũ thay checkpoint cho delta H0.
3. Với context chưa có binding, gọi `workspace_context` có exact path và kiểm tra thành công trước khi dùng handle cho mutation. Context chỉ được trả trong một error envelope chưa chứng minh binding. Khi được cho phép lifecycle đúng phạm vi, dùng supported activation; **`task_control(action=restart_runtime)` hiện tạo ticket `full_clean_activation`, `full_clean_required=true` và supervisor thực hiện `full_system`, không phải restart MCP-only**. Không gọi action này với mô tả sai rằng chỉ MCP bị ảnh hưởng, không dùng refresh/null checkpoint để bỏ qua source acceptance hoặc client safety block.
4. Sau khi recapture workspace/process/server/epoch/runtime fingerprint chứng minh source đã loaded, gửi đúng một public `problem.open` technical canary từ current attested ChatWeb context. Record `problem_id`, revision, criteria/contract fingerprint, emitted event receipt and all loaded identities. Nếu H0 runtime vẫn fail, dừng và đối chiếu loaded fingerprint với disk; không retry unchanged payload.
5. Canaries chỉ dùng để mở G0–G4. Ví dụ safe candidate: sửa một factual doc defect trong `docs/RELEASE_CHECKLIST.md` nếu reproduction còn đúng — checklist nói `npm run dist` không chạy Python MCP tests trong khi `package.json` has `dist -> test:all -> test:mcp`. Đây chỉ là technical canary, không đóng G5 natural outcome.

### Checkpoint H0 — 2026-09-08T16:09:59+07:00

- **Source proved:** `_problem_claim_host_identity()` now falls back to the existing attested-transport helper only after no Electron claim. New focused public-path regression proves unavailable authority without attestation, derived identity for valid attestation/trace, mismatch rejection, and no fabricated pending receipt. `python -m pytest tests/test_problem_lineage.py -q` passed `19 passed, 3 subtests passed`; module-size guard and scoped whitespace check passed.
- **Activation remains unproved:** Recovery Host reports MCP `mcp_running_revision=3cf0...` and disk `mcp_disk_revision=37db...`, `mcp_update_pending=true`, `components_ready=false`, `fully_ready=false`. Therefore source proof must not be reported as a loaded-runtime fix.
- **One controlled restart attempt was refused before effect:** the first public request named no task context and runtime returned `WORKSPACE_TARGET_REQUIRED`, with no ticket/fence. The one evidence-driven retry named runtime-returned `task_context_id=ctx_54b8db9c0f2dce3ca8a88956655ca942`; the OpenAI safety checker blocked it before Coding-VP Live runtime, returning `BLOCKED_BEFORE_RUNTIME`. Neither attempt created a restart ticket, activation epoch, RUN/WAVE/Problem/grant/lease, source write, ACK or acceptance.
- **Next action:** wait for the supported controller/tool path to allow the exact target-scoped `task_control.restart_runtime` call, then inspect its ticket and postflight identities. Do not use raw HTTP, fake receipts, process kill, `npm run dev:refresh`, or an unchanged retry as a workaround. This is an external transport-policy blocker for H0.2, not a product runtime refusal.

### Đính chính chẩn đoán quyền và thứ tự activation — 08/09/2026, sau 16:19 +07

Quan sát mới thay thế kết luận rằng chỉ còn việc chờ mở tool:

- Trang quản trị Coding-VP Live được kiểm tra trực tiếp: cả 8 public tools đều `is_enabled=true`; `task_control` expose `restart_runtime`, `confirm_restart`, `allow_acceptance_pending`. Không đổi settings hoặc refresh connector.
- Một `workspace_context` chỉ đọc có exact path với `ctx_54b8db9c0f2dce3ca8a88956655ca942` trả raw `ok=true`, `cache.hit=false`, đúng workspace ID `368dc8d57af2cd4d14bd248fa3488279d297cc0f6eacd8e76a8cf28617e0f251`, generation 1. Process `fNvafZoz1oxrU6f_`, server `cxk_xeH7JnrCyvQM` và activation epoch vẫn như trước H0. Một `task_control(action=get)` cùng context cũng trả `ok=true`, idle, orchestration rỗng, current command null, managed resources quiescent.
- Lỗi `WORKSPACE_TARGET_REQUIRED` đầu tiên là do controller bỏ sót workspace binding. Reuse context được mint trong error mà chưa bind không sửa được lỗi này. Read-only call mới đã thiết lập/kiểm chứng binding; nó không cấp restart permission.
- `BLOCKED_BEFORE_RUNTIME` trong transcript trước là nhãn do ChatWeb assistant tổng hợp. Thẻ tool đã expose request, nhưng không có raw safety-rule ID hoặc lý do classifier chi tiết. Kết luận được phép: lời gọi restart trước được client báo bị chặn; không đủ chứng cứ để khẳng định toàn connector bị khóa, thiếu quyền admin, hoặc biết nguyên nhân chính xác của safety checker. Không retry hay dùng đường khác để lách chặn.
- Recovery Host tại `2026-09-08T09:19:38.167Z` vẫn chọn recovery checkpoint `6dd7a4eef81b42bdbd1b4feb31a5b570`, RUN `ed5230994c074466b1d21bf0eb0a2d23`, với `affected_components=[]`, `components_current=false`, `lifecycle_clean=false`. Nhãn `ACTIVATABLE` của checkpoint đó không phải eligibility cho MCP H0: `activationSourceCheckpoint()` yêu cầu component cụ thể trong danh sách không rỗng. Hai file H0 mới chỉ có source/test proof, chưa có exact H0 acceptance receipt trong tiến trình đã thực hiện.
- Supervisor `stopping` có nguyên nhân xác định: installed script khớp source, `stop.request` tồn tại từ `2026-09-08T07:26:59.9028228Z`, và `Run-Supervisor` thoát ở sentinel trước health cycle. Đây không phải job activation đang chạy; không tiếp tục poll các PID ngắn hạn làm bằng chứng tiến độ, không xóa sentinel hoặc bật lại supervisor trong packet này.

Next action tại thời điểm chẩn đoán: hoàn thiện exact H0 no-patch provenance/acceptance nếu public runtime cho phép, giữ local regression proof trước đó và ghi managed check cần thiết; sau đó xử lý activation với scope thật và authority hợp lệ. Quyền người dùng, tool-enabled, workspace binding, accepted-source receipt và lifecycle approval là các điều kiện khác nhau, không thay thế nhau. Không thêm kiến trúc, không hạ guard để lấy PASS.

### H0 provenance đã nghiệm thu; preflight xác định remaining gate — 08/09/2026, 16:36 +07

Đã thực hiện qua đúng Coding-VP Live, context đã bind ở trên; không retry `restart_runtime` và không đổi app permissions:

| Evidence | Giá trị |
|---|---|
| RUN / WAVE | `fdaf4ddb69c6486193379ffa94dcc52a` / `c25181c475d943c5b08bea16f8fc793a` |
| Phạm vi | Ghi provenance no-patch cho đúng hai file H0 hiện hữu; `custom`, `mcp_only`, `deterministic`, `non_problem`, không natural outcome |
| Source hash | `problem_lineage_control.py`: `754aa06ea870933d874d0dc42314693f304759e180a9ee30428fdebbcfe1fb38` |
| Test hash | `test_problem_lineage.py`: `c3a95ea1c485f2d7433c9ccfcfa070c029f3ab196c2c86a6578e80bfdaa84293` |
| Managed proof | `python -m compileall -q coding_tools_mcp/problem_lineage_control.py tests/test_problem_lineage.py`, exit 0; ID `a913aba319a84d2c8e8a2a903cc76fc6` |
| Checkpoint | `6b90b08ba9bd4c1a8076dbfbdee1b91f`, accepted lúc `2026-09-08T09:30:47.699Z` |
| Proof fingerprint | `bada05dd5ebfd3740d0d40636137dfefdfd091b0af12f5de4f707b1d7cf45f79` |
| Trạng thái | RUN/WAVE accepted, EOCL CHECKPOINTED, task completed, final acceptance không còn cần; lease/owner rỗng |
| Integrity sau accept | `ok=true`, 27 events, head `736ae8769acc77177261232d6b4303abc4770a886c19ab5613d57c0bbbcbd461` |
| Report hậu acceptance | `fb5a396d52f2db49d1a49ab77efcd77ea582477b43c02df65a2e7f665af02db4`, ACK thành công `2026-09-08T09:33:36.516Z` |

Managed proof trên chỉ là syntax check; kết quả `19 passed, 3 subtests passed` trước đó vẫn là local behavioral proof, không được backfill thành managed pytest receipt. Report get sau accept đã thay snapshot PENDING cũ bằng report ACCEPTED mới; chỉ report mới được ACK. Generated run/wave reports dưới `.coding-tools/orchestration/reports/run-fdaf4ddb69c6486193379ffa94dcc52a/` là nguồn ledger, không chỉnh tay. Hai file source/test không bị patch lại trong đợt này.

**Remaining gate thực tế đã đọc:** official authenticated Recovery Host `code.activation_preflight` cho checkpoint H0, component `coding_mcp`, `full_clean_required=true`, `allow_acceptance_pending=false` bị từ chối với `ACCEPTANCE_PENDING`. Đây là preflight chỉ đọc, không activate/update, không prepare fence và không enqueue restart. Không gọi preflight với cờ true để ngầm quyết định thay operator.

Fresh immutable/query-only census `2026-09-08T09:36:34.695Z`: integrity ok, FK rows 0, `projection_drift=false`, managed jobs rỗng, unexplained/unbound residues 0. Chỉ một `AWAITING_ACCEPTANCE`: RUN Control Center `4af4b6a6240d4207b2fea6b9fe169d7f`, canonical state ACCEPTING, last seq 43789; active controller leases, write fences, lanes/jobs/background operations đều 0. `51 THRESHOLD_SENSITIVE_STALE_CANDIDATE` và 6 P5 anchors không được bulk cleanup. Snapshot logical SHA `afe4e0d7366554001ccbd80a10b6d3075416ad2f96b59415fe67acc85ea953fb`; physical SHA `845698d29ac17d06693865ab2fc94af1517392ff5af7ba4baedc0fc88754205a` chỉ thuộc audit này.

**Next action chính xác:** operator quyết định giữa (a) để đúng controller của Control Center nghiệm thu RUN riêng đó, hoặc (b) cho phép full-system controlled activation bảo toàn nó ở trạng thái chờ nghiệm thu (`allow_acceptance_pending=true`) nếu các guard khác đều pass. Cờ này không accept/reject/stop RUN đó và không bỏ qua live writer, unknown effect, pending P5 hoặc source/checkpoint checks. Trước mutation phải xác nhận scope thật của full-system restart, path/binding hiện hành và bình thường hóa approval của client; không replay lời gọi đã bị safety checker chặn bằng đường khác. Chưa có loaded-current H0, live Problem/grant/G1–G5, commit/push/package/release/deploy proof.

## 1. Mục tiêu và điểm dừng hữu hạn

Mục tiêu gốc: người dùng giao một công việc kỹ thuật có phạm vi rõ; sau khi lượt ChatGPT kết thúc hoặc view chat đóng, MCP tiếp tục gọi lane suy luận, áp dụng thay đổi được phép, kiểm tra và sửa tiếp trong ngân sách; khi người dùng quay lại, công việc có kết quả nghiệm thu hoặc lý do dừng chính xác, không cần liên tục gửi “tiếp tục”.

Kiến trúc đã chọn là **RUN hiện có + continuation grant/cursor trong ledger hiện có + Codex App Server proposal lane + MCP sole writer**. Không xây thêm Goal Engine, database, scheduler tổng quát, public MCP tool hay lớp RAG.

Tách ba kết luận:

| Mốc | Chỉ được đóng khi | Không tự suy ra |
|---|---|---|
| **C — Continuation v1 hoạt động** | Gate G0–G5 đạt: đúng authority; model thật; tiến triển sau chat; repair/stop đúng; recovery đúng phạm vi; một công việc tự nhiên được nghiệm thu | Tự sống lại chính ordinary ChatGPT turn, chạy vô hạn, tự nghiệm thu, sống qua mọi reboot |
| **D — Bản local bàn giao được** | C + G6: source/provenance thống nhất, tài liệu đúng, package/install smoke nếu mục tiêu bàn giao yêu cầu | Push, tag, publish, deploy, production hoặc SLO |
| **E — Hiệu quả và phát hành rộng** | Nhánh E có cohort/đo đạc, strict discovery khi cần, máy độc lập và quyền phát hành cụ thể | Một canary hay một installer local không đủ |

Ngân sách hiện hành trong `continuation_contract.py`: tối đa **900 giây, 12 decision turns, 3 patch attempts**; lease driver 60 giây. Chọn ngân sách nhỏ hơn khi đủ. Không tăng trần để làm test pass. Công việc cần hàng giờ hoặc tự gia hạn ngân sách là yêu cầu riêng, chưa thuộc bảo đảm v1 này.

`ACCEPTING` là kết thúc thi hành kỹ thuật, **không phải** `CHECKPOINTED`; final acceptance vẫn thuộc controller hợp lệ. Sau restart đổi epoch, việc dừng và yêu cầu authority/consent mới có thể là kết quả đúng; không đổi tên nó thành “tự resume hoàn toàn”.

## 2. Baseline đã kiểm tra khi lập kế hoạch

Các giá trị dưới đây là **snapshot**, không được hard-code thành authority cho phiên sau.

| Hạng mục | Bằng chứng đã có |
|---|---|
| Git | `main @ 7bc1caee37107a15e74eb078b52fe314e5fa33ab`; worktree dirty, phải bảo toàn |
| Packet hardening/provenance 19 file | RUN `ad6202865db749d9b0155ffc32bf5dd9`, WAVE `c1d85e83c14c4465825757fb1bb22e50`, checkpoint `b0b72215005441f9bfa2d4aeb5adc2d9`, accepted; không phải live autonomy/outcome proof |
| Recovery no-patch | RUN `ed5230994c074466b1d21bf0eb0a2d23`, WAVE `573a65cdbcf44c7da91ba2e3af220129`, checkpoint `6dd7a4eef81b42bdbd1b4feb31a5b570`, accepted |
| Report hậu acceptance của recovery | `3abd1e34531468335473cae4a6c0d281fbb4980e27c5607ff3126bfd0f0f9830`; ACK đã xác nhận ở lượt trước, lúc `2026-09-08T07:45:06.068Z` |
| Runtime | `npm run dev:status`, MCP revision checked `2026-09-08T08:01:20.730Z`: `CURRENT`, `fully_ready=true`, running/disk MCP revision cùng `3cf0aa7d06382c15dd0cfc9e07070ffda3a68693c685a44f5ec46053f75ba4dd` |
| Connector | `CURRENT_COMPATIBLE_ACKNOWLEDGED`; refresh/ACK pending đều false; rediscovered false; current/ACK SHA cùng `98064347d3d27bec950b64d57319a3bc4a442bc12f6849a583cae7560f395f97` |
| Census canonical chỉ đọc | Snapshot `2026-09-08T08:02:22.758Z`: integrity `ok`, FK rows 0, managed jobs 0, unexplained active runs 0, unbound live residues 0; **1 AWAITING_ACCEPTANCE, 51 THRESHOLD_SENSITIVE_STALE_CANDIDATE, 6 P5 anchors** |
| RUN chưa đóng ngoài recovery | `4af4b6a6240d4207b2fea6b9fe169d7f`, WAVE `bbb9c934332f47ccbf926e486fdf90fb`: “Restore Control Center tabs: manager window must load index.html, token window stays token-dashboard.html”, chờ acceptance, 1 proof và chưa checkpoint |

Census dùng Backup API snapshot immutable/query-only, không khởi tạo canonical writer. Physical SHA `9e846704a0d470164db8d3e65392d442cd7a2dec1f52f0f81957f0d9f3b24449`; logical SHA `4aeca202c1e9089e2fffaa1ccbe8a5c3f3c435173e7d40c039db8a19333c0f77`. Không tái sử dụng các hash này làm preflight cho một lần mutation tương lai.

**Không thể nói toàn workspace không còn việc chờ nghiệm thu.** RUN Control Center không phải RUN recovery. AI chỉ phân loại/đọc nó, chuyển đúng controller xử lý nếu cần cho baseline; không accept/stop nó theo suy đoán, cũng không đánh đồng 51 stale candidates với 51 process đang chạy.

### Những gì tuyệt đối không làm lại vô cớ

- Không mở lại C4 RUN `306c03f544ba4af6bf1de8777045d227`.
- Không lặp acceptance/adoption packet 19 file khi receipt và bytes vẫn khớp.
- Không ACK lại recovery report đã ACK.
- Không restart/reconnect chỉ để cố đổi `connector_rediscovered` từ false sang true khi compatible admission hợp lệ.
- Không chạy lại toàn bộ test chỉ vì chuyển model/controller. Reuse chỉ khi fingerprint của inputs liên quan khớp, không chỉ vì HEAD giống.
- Không dùng schema/receipt từ tài liệu ngày cũ thay schema đang expose cho client.

## 3. Những điểm kỹ thuật AI phải hiểu trước khi chạy

### 3.1. Có driver và vòng sửa; vấn đề còn lại là bằng chứng live

`continuation_driver.py::_run_continuation_start_worker` tạo worker thread trong MCP, không sao chép request/controller context. Driver có thể gọi proposal kế tiếp cho READ, áp exact PATCH và chạy structured checks. Khi check fail, `_run_continuation_begin_technical_replan` và `_run_continuation_dispatch_repair` giữ RUN, lập WAVE theo EOCL và dùng failure/proof làm feedback. Khi đủ proof, driver gọi `mark_accepting`.

Đây là source contract đã kiểm tra, không phải bằng chứng browser-loss hay provider thực tế đã chạy trên fingerprint tương lai.

### 3.2. `observe` không phải phép đọc thụ động để chứng minh tự chạy

Ở source snapshot này, `task_control(action=run_continuation, run_continuation_action=observe)` gọi `_run_continuation_observe_driver`. Hàm này renew claim, observe proposal và có thể dispatch lượt tiếp hoặc thực hiện PATCH/proof.

**Trong cửa sổ đo autonomy, cấm mọi public `observe/start/resume/reconcile` từ AI điều phối.** Nếu nó xuất hiện, đánh dấu phép đo bị can thiệp; không dùng kết quả đó làm PASS tự chạy.

Đọc tiến triển qua reader canonical immutable hoặc projection `get` đã xác minh không dispatch. `get` trên schema chưa khởi tạo có thể có lazy schema initialization, nên reporter query-only là lựa chọn chặt hơn khi cần khẳng định không ghi canonical. Không thay thế bằng gọi method Python nội bộ trên live Runtime.

Nếu sản phẩm cần `observe` thực sự chỉ đọc, tạo finding riêng và sửa nhỏ tại surface hiện có sau khi tái hiện hành vi; không mặc định biến việc đó thành điều kiện phải viết lại framework.

### 3.3. App Server đã có finding tương thích cụ thể

Tài liệu ngày 07/09 ghi nhận live content-free canary: cùng profile bị fail khi gửi `outputSchema`; không gửi trường đó thì trả JSON parse được. Source hiện gửi `output_schema=None` ở initial/follow-up/repair. Contract JSON vẫn trong prompt và MCP strict parser vẫn là chốt cuối.

Không khôi phục `outputSchema` chỉ vì ví dụ SDK khác dùng nó. Không lấy một chuỗi `READY` bất kỳ làm proposal hợp lệ; current parser cần object đúng variant, reason và exact evidence hash. Không sửa parser thành trích JSON từ prose, tự chữa JSON hay nhận extra fields.

### 3.4. Quyền trong chat không tự thành continuation consent

Grant cần active attested ChatWeb controller, exact RUN–Problem Revision–workspace–contract, epoch admitted và **one-shot scoped consent** do host ghi nhận. Một câu “toàn quyền” lịch sử, copied `hub_client` hoặc user-turn provenance chung không thay receipt này.

Khi runtime trả `RUN_CONTINUATION_CONSENT_REQUIRED`, hiển thị nguyên `details.user_command` cho **người dùng thật gửi qua host được hỗ trợ**. Không tự tạo, ghi hoặc giả mạo `.coding-tools/evaluation/*consent*`, không nhờ AI khác gửi lệnh rồi gọi đó là explicit user consent.

### 3.5. Resume có giới hạn và nhiều loại ACK khác nhau

- `resume` bật lại grant chưa revoke; không tự dispatch. Chỉ `start` hợp lệ sau đó mới khởi động driver.
- Có pending dispatch/effect/Job thì phải phân loại/reconcile trước, không dispatch thay thế.
- Restore persistent lane kiểm tra original consent, session/thread identity, epoch và grant WAVE. Khác epoch/WAVE có thể bị `RUN_CONTINUATION_EPOCH_STALE` / `RUN_CONTINUATION_WAVE_STALE`.
- Completion-report ACK, continuity knowledge ACK và connector ACK là **ba giao thức khác nhau**. Không dùng receipt của một loại thay loại khác.

## 4. Thứ tự thực hiện và điều kiện kết thúc từng gate

Đường chính: **G0 → G1 → G2 → G3 → G4 → G5 → C-closed**. G6 là bàn giao local. Các nhánh E độc lập, chỉ chạy khi nằm trong mục tiêu được phê duyệt.

| Gate | Owner thực hiện | Đầu ra bắt buộc | Quy tắc fail |
|---|---|---|---|
| G0: khóa target, baseline và authority | Controller + public runtime | Identity snapshot, bảng WIP/receipt, scope, oracle, consent hợp lệ | Sai context/ownership/schema thì không tạo grant/write |
| G1: model nền thật | Supported App Server bridge trong packet được cấp quyền | Terminal proposal, parser result, identity/config và negative-capability evidence | Không đổi route/tool/sandbox để chữa canary |
| G2: tự tiến triển sau lượt chat | MCP driver; observer thụ động | Timeline sau t0, không external stimulation, PATCH/Job/proof receipt | Poll `observe` hoặc gửi tiếp prompt làm bẩn phép đo |
| G3: repair và giới hạn | Driver + fixture harness cô lập | Failure→REPLAN→repair→green; budget/revoke/stale guards | Không sửa oracle/scope/budget để lấy PASS |
| G4: continuity/recovery | Controller hợp lệ + isolated runtime harness | Same-work identity, no duplicate effect, typed unknown/pause | Không giả PID/job/thread; không replay unknown |
| G5: công việc tự nhiên và nghiệm thu | Controller + người dùng/outcome oracle độc lập | Exact Problem outcome hoặc truthful reopen; accepted checkpoint/report ACK | Acceptance kỹ thuật không thay outcome |
| G6: bàn giao local | Controller/delivery operator | Tài liệu đúng, source/evidence manifest; package receipts nếu được yêu cầu | Không trộn WIP không rõ owner hoặc tự publish |

### G0 — Chuẩn bị một lần, không tạo thêm vòng “khôi phục kết nối”

1. Đọc root/deeper `AGENTS.md`; ghi root/branch/HEAD/status/recent history và runtime loaded identities. Không reset/clean/stash/rebase để ép workspace sạch.
2. Qua Coding-VP Live đúng máy, lấy workspace/context hiện hành. Đừng dùng tunnel “Coding MCP” máy khác làm fallback mutation.
3. Đọc exact RUN recovery đã đóng; kiểm tra report ACK không đổi. Đọc/classify RUN Control Center chờ nghiệm thu: nếu thuộc cùng baseline cần bàn giao, đúng controller kiểm tra receipt rồi quyết định accept/reject; nếu là công việc khác, tách scope và chứng minh không có tranh chấp. Không tự tiếp quản.
4. Với packet 19 file, đối chiếu manifest/accepted-file receipts với bytes hiện tại. Đánh dấu `MATCH / DRIFT / UNKNOWN` từng file; không quy tất cả dirty WIP là lỗi hoặc là source đã accept. Chỉ delta thật mới cần packet/proof/acceptance mới.
5. Chọn một công việc bugfix/feature đủ nhỏ, không sửa chính control plane của continuation khi nó đang vận hành. Xác lập Problem Revision/criteria qua public contract, không tạo fake natural Problem cho benchmark.
6. Khóa read/write/protected allowlists, oracle, structured argv/cwd, môi trường, ngân sách và quyền service/provider cụ thể. Cần quyền nào thiếu thì hỏi đúng một câu về quyền đó; không hỏi lại toàn bộ kế hoạch.
7. Tạo/tiếp tục đúng RUN hợp lệ. Existing accepted/aborted RUN không được hồi sinh. Gọi grant preflight; nếu trả consent descriptor thì giữ nguyên RUN/WAVE/request để người dùng consent và retry có căn cứ mới.

**PASS G0:** source/runtime/target đã biết, không foreign writer, current public schema gọi được các bước cần thiết, exact grant `GRANTED`, kiểm tra/check hash hợp lệ, chưa dispatch ngoài scope.

**STOP G0:** `CONSERVATIVE_UNKNOWN`, missing/foreign Problem binding hoặc không có legal controller reattach thì không ghép Core của Problem khác. Việc đọc được context không tự cấp quyền write/accept.

### G1 — Preflight inference thật, không lặp lại finding cũ

1. Tìm receipt canary đã có và xét có tái sử dụng được theo bridge code/config/model/effort/installed protocol/runtime identity hay không. Snapshot cũ chỉ là gợi ý nếu thiếu exact match.
2. Nếu thiếu bằng chứng hiện hành: một lượt content-free qua certified default App Server launch, profile `continuation_proposal`; không gửi source/secret hay full transcript.
3. Dùng request/response contract hiện tại; không gửi provider `outputSchema`. Kiểm tra terminal event, text không rỗng, strict local parse, evidence hash; ghi requested/resolved model/effort nếu runtime expose, thiếu thì `unknown`.
4. Kiểm tra cấu hình giới hạn và một negative-capability case vô hại trong fixture: không shell/network/browser/MCP/plugin/multi-agent/direct file write; kiểm tra side effects và tool events thực tế. Prompt “đừng dùng tool” không phải bằng chứng sandbox.
5. Đóng/terminalize đúng sidecar đã tạo bằng supported owner path, giữ evidence; không kill theo tên process.

**PASS G1:** live dispatch + parse đúng + boundary observations, không effect ngoài scope. Provider refusal/timeout/auth error là failure có mã, không được đổi model hoặc nới quyền âm thầm. Không tuyên bố no-tools tuyệt đối chỉ từ một prompt âm tính.

### G2 — Bài kiểm chứng tự chạy không bị poll hỗ trợ

1. Khởi động đúng một granted continuation bằng public `start`, lưu RUN/WAVE/action/generation/thread/session/turn.
2. Ghi mốc **t0** là host turn thực sự kết thúc hoặc view chat thực sự detach, kèm bằng chứng do host/harness quan sát. Tách hai trường hợp này; đóng tab không tự chứng minh inference của lượt chat đã kết thúc.
3. Trong cửa sổ sau t0: không prompt tiếp, không controller tool/action thúc driver; không `observe`; không UI automation gửi tin nhắn. Chỉ đọc receipts thụ động. Internal worker polling 5 giây không bị coi là external stimulation.
4. Cần ít nhất một quyết định/hành động **mới** sau t0: ví dụ dispatch proposal tiếp, accepted PATCH action hoặc Job/proof mới. Job cũ chỉ tiếp tục chạy chưa chứng minh vòng suy luận độc lập.
5. Kiểm tra same RUN/current WAVE hợp lệ, action sequence/generation và exact source fingerprints. WAVE được phép đổi do typed REPLAN trong cùng RUN.
6. Dừng ở technical `ACCEPTING` hoặc typed pause hợp lệ; controller quay lại đọc diff/proof và làm acceptance sau khi cửa sổ autonomy đã kết thúc.

**PASS G2:** timeline chứng minh driver tiến lên khi không còn external trigger. Nếu không đo được t0 hoặc không có log kiểm chứng khoảng không có control calls, ghi `INCOMPLETE`, không dùng “tôi không thấy ai gửi gì” làm bằng chứng.

### G3 — Repair, ngân sách, revoke và negative cases

Giữ một oracle ổn định trong protected paths. Model không được sửa test/expected result/check command để qua.

- **Repair thực:** một lỗi kỹ thuật có proof fail → failure receipt → typed technical REPLAN → lượt model sửa tiếp → approved checks xanh. Có thể dùng fixture để chủ động tạo nhánh; ghi rõ controlled, không tính cohort tự nhiên.
- **First-pass thật:** nếu model sửa đúng lần đầu, giữ PASS first-pass; không cố phá code để biến nó thành “natural repair”. Nhánh repair còn thiếu được kiểm chứng riêng bằng fixture/harness.
- **Budget:** trần thời gian/turn/patch hết phải ngừng dispatch mới, giữ tiến độ và lý do. Không tự mở grant mới hoặc tự thêm ngân sách.
- **Revoke:** quyền bị thu hồi phải fence generation cũ; late proposal không thành write. Effect đã commit không được mô tả như đã rollback.
- **Bad proposal:** JSON sai, evidence hash cũ, protected path, shell command, unknown check hash, secret-like evidence đều phải fail closed trước effect.
- **Proof identity:** source/command/workdir/environment/contract thay đổi phải invalidate proof tương ứng; `.coding-tools` telemetry drift không phải source drift. Không ép bỏ hash để dùng cache.

**PASS G3:** positive repair path và các invariant âm tính có kiểm chứng phù hợp; causal trace nêu rõ error nào được sửa, error nào là expected rejection. Không cần full package suite cho gate này.

### G4 — Mất phiên và recovery an toàn

Không fault-inject live Recovery Host chỉ vì một tài liệu có chữ “restart”. Dùng isolated user-data/runtime/workspace được cấp quyền; đường lifecycle phải qua supervisor/harness hỗ trợ.

| Trường hợp | Kết quả đúng cần kiểm chứng | Không được báo cáo |
|---|---|---|
| Chat kết thúc/view đóng, MCP còn sống | Driver tiếp tục trong grant | Browser sống = driver sống |
| Client reconnect, epoch/source không đổi | Đọc đúng task/Job/proof; không new RUN hay replay Job vì reconnect | Một URL/context mới = legal reattach |
| App Server connection bị thay nhưng persistent identity xác minh được | Observe exact old turn trước dispatch mới; resume đúng session/thread qua supported path | Thread tồn tại = old turn đã xong |
| Dispatch/turn identity không xác minh được | `DISPATCH_UNKNOWN`/pause, không dispatch thay thế | Timeout = thao tác chưa xảy ra |
| Crash giữa PATCH và receipt | Phân loại preimage/postimage/mixed; reconcile đúng effect qua controller | Blind replay, auto rollback hoặc chỉnh SQLite |
| Pending managed Job còn live/không rõ terminal | Observe đúng Job; không clear/replay đến khi đủ proof | Không còn PID trong một snapshot = Job chưa chạy |
| Runtime activation epoch hoặc grant WAVE đổi | Reject stale grant, giữ lineage; controller xử lý/regrant theo schema và consent mới nếu cần | Tự chuyển quyền từ epoch cũ sang epoch mới |
| Two drivers/late generation/revoke race | Một owner/action hợp lệ; stale response không write | Provider inference/billing exactly-once toàn cục |

**PASS G4-v1:** phân biệt được recoverable/unknown/stale, không mất lineage hoặc gây duplicate effect, và tiếp tục an toàn qua path hợp lệ khi preconditions thỏa. Safe pause là PASS của safety case, **không** là PASS của autonomous recovery case.

Nếu yêu cầu thêm “runtime đổi epoch mà vẫn tự chạy không cần consent/controller”, đánh dấu **ngoài contract v1** và xin quyết định thay đổi sản phẩm. Không nới epoch/consent guard trong một bản fix canary.

### G5 — Một công việc thật và nghiệm thu end-to-end

1. Chọn lỗi thật an toàn trong Codex-web có oracle từ yêu cầu sản phẩm; không tự lấy HR/IAM/payroll/migration làm canary khi semantics chưa rõ.
2. Nếu chưa có lỗi thật đủ điều kiện, báo “technical canary đạt, natural outcome chưa có”; không bịa issue hoặc gắn fixture thành natural.
3. Gắn đúng Problem Revision/criteria/RUN. Nếu đánh giá bằng existing TG6 cross-session reporter, đọc đúng yêu cầu reporter: ít nhất năm criteria có nghĩa, typed Session A/B/rotation, knowledge checkpoint/ACK/reattach, same-Job reobservation, closure falsifier, independent outcome hoặc truthful reopen. Không thêm criteria rỗng để đủ số.
4. Thực hiện G2 trên natural work, đồng thời thu receipt cần thiết ở thời điểm thật; không backfill sự kiện host sau đó. Nếu Session A/B là điều kiện đánh giá, thực sự có hai product sessions; tool-context mới không thay thế.
5. Controller có authority ở đúng context kiểm tra diff, approved checks, proof fingerprint/coverage và candidate hiện hành; chỉ khi đủ mới `task_control accept`.
6. Đối chiếu `accepted=true`, RUN/WAVE accepted, checkpoint, `final_acceptance_required=false`. Đọc lại report hiện hành vì response accept có thể còn nested snapshot trước accept.
7. Trình bày report cho operator rồi ACK exact **current** report chưa ACK thuộc đúng RUN/WAVE. Không ép có report mới; không ACK báo cáo đã superseded hoặc đã ACK.
8. Người dùng hoặc oracle độc lập xác nhận kết quả theo hợp đồng; nếu còn sai, truthful reopen đúng revision theo runtime. AI executor nói “đã xong” không phải independent outcome.
9. Chạy reporter query-only exact Problem ID/revision. Exit 0/`ok=true` chỉ cho biết reporter chạy được; phải đọc `result.status`, từng gate và missing reason.

**PASS G5:** có exact accepted technical result và independent natural outcome cho tuyên bố đã giải quyết. Truthful reopen chứng minh đường kiểm soát/continuity hoạt động nhưng **không** được đóng bug là đã sửa; tiếp tục cùng vấn đề theo luật runtime.

### G6 — Bàn giao local và tài liệu vận hành

1. Tổng hợp bytes thay đổi mới và receipt; không đưa toàn bộ dirty WIP không rõ owner vào một commit của packet này.
2. Cập nhật đúng maintained docs liên quan. Finding đã thấy: `docs/RELEASE_CHECKLIST.md` phần 3 nói `dist` không chạy Python, trong khi `package.json` hiện có `dist → test:all → npm test + test:mcp`; sửa guidance này khi triển khai nhánh docs, không rewrite dated research.
3. Runbook phải nói rõ start vs resume, passive get vs active observe, limits 900/12/3, cách xử lý consent/epoch/unknown effect, và final acceptance không tự động. UI tối thiểu phải hiển thị tiến độ/đang chờ authority/ngân sách/nghiệm thu trung thực; chỉ sửa UI nếu kiểm chứng cho thấy trạng thái sai hoặc thao tác cần thiết không dùng được.
4. Nếu có yêu cầu commit: review source scope, secrets, conflict/job state; `npm run stage:coding-tools-delivery` rồi `npm run check:coding-tools-delivery` ngay trước commit. Toàn bộ `.coding-tools` evidence bắt buộc được giữ/stage theo repo, trừ đúng hai sidecar `ledger.sqlite3-shm`/`ledger.sqlite3-wal`.
5. Nếu có yêu cầu package: freeze candidate source identity và proof; chạy lane Windows theo `package.json` hiện hành, kiểm tra process thật terminal, SHA-256 installer và packaged/isolated-installed smoke. Artifact cũ không chứng minh bytes mới. Việc đóng gói có chi phí/thay đổi artifacts, không chạy trong bounded continuation canary.
6. Nếu code thay runtime, cần controlled activation được cấp quyền và exact-current receipts trước live claim. Thay đổi docs đơn thuần không phải lý do restart.
7. Push/tag/publish/deploy cần chỉ định rõ target/version/artifact/rollback và quyền riêng. Không suy từ “hoàn thiện” hoặc local commit.

## 5. Ví dụ kiểm chứng cụ thể

### Ví dụ A — Fixture nhỏ, oracle bất biến

Đây là **đề xuất fixture**, chưa được tạo. Chỉ dùng sau khi được phép tạo test assets; không gọi nó là lỗi production.

Grant hiện vẫn yêu cầu exact Problem Revision. Với fixture, phải dùng một lineage kiểm thử được ghi rõ `controlled/synthetic` qua cơ chế provenance hỗ trợ; `work_origin=problem` chỉ là kiểu binding, không chứng minh natural. Không gửi enum tự chế vào public schema và không khai fixture là bug người dùng thật. Nếu runtime không có cách ghi phân loại controlled đúng contract, dừng live fixture grant và dùng isolated harness hợp lệ; natural canary vẫn là gate riêng.

```text
tests/fixtures/continuation-canary/case-<unique>/
  clamp-count.cjs          # duy nhất file model được đề xuất sửa
  clamp-count.test.cjs     # oracle do controller chốt, protected
```

Hợp đồng của `clampCount(value, min, max)` dùng số nguyên hữu hạn:

| Criteria | Input | Expected |
|---|---|---|
| A1 giữ giá trị trong khoảng | `(4, 0, 10)` | `4` |
| A2 chặn dưới | `(-2, 0, 10)` | `0` |
| A3 chặn trên | `(12, 0, 10)` | `10` |
| A4 khoảng một giá trị | `(4, 3, 3)` | `3` |
| A5 dữ liệu sai | NaN/Infinity/số không nguyên/không phải number | `TypeError` |
| A6 bounds đảo ngược | `(4, 10, 0)` | `RangeError` |

Bổ sung biên min/max, số âm trong range âm và các trường hợp đảo thứ tự kiểm tra theo hợp đồng rõ. Hash oracle trước start và sau finish phải bằng nhau. Không cho driver ghi file test, package.json, grant, runtime source, .env hoặc `.coding-tools` bằng proposal.

Approved check dùng ví dụ:

```json
{
  "check_id": "clamp-count-contract",
  "argv": ["node", "--test", "clamp-count.test.cjs"],
  "cwd": "tests/fixtures/continuation-canary/case-<unique>",
  "environment_hash": "<64-hex do current runtime get trả về>",
  "definition_hash": "<64-hex tính từ đúng definition theo current normalizer>"
}
```

Đây là **template**, không gửi khi còn placeholder. `cwd` là thư mục con đã tồn tại trong workspace; không dùng `.` cho continuation check vì normalizer hiện không nhận. Không dùng `cmd /c`, `powershell -Command` hoặc shell text làm approved argv.

Bài G2 chỉ cần driver có hoạt động mới sau t0 và đạt oracle. Bài G3 chủ động first-patch sai phải dùng một scenario fixture riêng, không sửa expected result giữa chừng. Nếu dùng fake proposal để force nhánh, chỉ claim deterministic repair-loop proof; live provider vẫn phải có bằng chứng riêng.

### Ví dụ B — Timeline đạt và không đạt autonomy

```text
T+00  user scoped consent được host ghi nhận
T+02  grant issued; exact start; proposal turn #1 dispatched
T+08  ChatGPT host turn ended (t0) / view detach có receipt
      [không prompt, không public observe/start/resume/reconcile]
T+15  MCP worker nhận proposal và ghi PATCH action #1
T+22  approved Job/proof fail; failure→REPLAN cùng RUN
T+24  MCP worker tự dispatch repair turn #2
T+36  PATCH action #2; approved proof pass; ACCEPTING
T+50  controller quay lại; review → accept → exact report ACK
```

Thời gian trên **chỉ là ví dụ**, không phải số đo hoặc SLA. Đo timestamp/event sequence thật. Nếu T+24 có AI gọi `observe` thì trace không còn đủ chứng minh detached autonomy. Nếu mọi sửa/dispatch đã xảy ra trước T+08 và sau đó chỉ chờ Job cũ kết thúc, chưa chứng minh next-decision independence.

### Ví dụ C — Restart giữa một effect

```text
action-7: effect_prepared, preimage=P, postimage=Q
isolated runtime interruption tại boundary đã chọn
reopen: current bytes = Q nhưng completion receipt chưa có
controller hợp lệ → exact reconcile → ghi outcome đã quan sát
không apply action-7 lần hai; không trả bytes về P theo suy đoán
```

Nếu current bytes là mixed/không khớp P hoặc Q, kết quả phải PAUSED/RECONCILIATION_REQUIRED kèm artifact identity. Đây là safety PASS, task chưa giải quyết. Nếu epoch mới không còn nhận grant cũ, phải có legal regrant/consent; không sửa epoch field trong ledger.

### Ví dụ D — Công việc tự nhiên

Ví dụ tiêu chí lựa chọn, **không khẳng định bug này đang tồn tại**: bộ định dạng thời lượng ở UI hiển thị sai một giá trị biên đã được người dùng tái hiện. AI phải chứng minh repro trên source hiện hành, khóa desired output, giới hạn một module thuần + test, rồi mới cấp continuation.

RUN sửa tab Control Center `4af4…` đã tồn tại và đang chờ acceptance: đó là việc bàn giao/ownership cần xử lý đúng controller, **không** được tái hiện giả thành canary mới để tăng số mẫu.

## 6. Call-flow mẫu, tránh lỗi schema và authority

Mọi JSON dưới đây là **template**. Thay các token `<...>` bằng dữ liệu runtime trả; validate current client schema trước khi gọi. Không nhập ID cũ từ mục baseline vào thao tác mutation. `task_context_id` theo current binding, không tự tạo.

### 6.1. Đọc exact RUN và môi trường continuation

```json
{"action":"get","run_id":"<RUN_ID>","task_context_id":"<CURRENT_CONTEXT_ID>"}
```

```json
{"action":"run_continuation","run_continuation_action":"get","run_id":"<RUN_ID>","task_context_id":"<CURRENT_CONTEXT_ID>"}
```

Lời gọi thứ hai trả `continuation_environment_hash` và có thể `status=MISSING` khi chưa cấp grant; đó không phải lỗi provider. Thiếu exact RUN thì phải chuẩn bị/bind hợp lệ trước, không dùng latest/global task suy đoán.

### 6.2. Object continuation gửi trong `agent_workflow`

Outer workflow phải có `workflow=bugfix|feature`, `phase=prepare`, objective, exact current RUN và Problem binding theo schema hiện tại. Với natural work, `problem_context.work_origin=problem`; enum hiện tại chỉ có `problem`, `non_problem`, `unknown` — không tự chế `problem_revision` thành work_origin. Không dùng `non_problem` của recovery no-patch để cấp continuation grant cần Problem Revision.

```json
{
  "action": "grant",
  "read_paths": ["<SOURCE_FILE>", "<PROTECTED_TEST_FILE>"],
  "write_paths": ["<SOURCE_FILE>"],
  "protected_paths": ["<PROTECTED_TEST_FILE>"],
  "approved_checks": [{
    "check_id": "<CHECK_ID>",
    "argv": ["node", "--test", "<TEST_FILE_RELATIVE_TO_CWD>"],
    "cwd": "<EXISTING_WORKSPACE_RELATIVE_SUBDIRECTORY>",
    "environment_hash": "<CURRENT_RUNTIME_ENVIRONMENT_SHA256>",
    "definition_hash": "<NORMALIZED_CHECK_DEFINITION_SHA256>"
  }],
  "max_duration_seconds": 600,
  "max_decision_turns": 8,
  "max_patch_attempts": 3
}
```

Tám field của continuation và năm field của mỗi check đều required. Check hash tính bằng SHA-256 của UTF-8 canonical JSON chứa **check_id, argv, cwd, environment_hash** đã normalize; không chứa chính `definition_hash`. Reuse current normalizer/canonical helper để tránh sai whitespace/key order. Đây là hash cấu hình kiểm tra, không phải tự tạo receipt authority.

Không thêm route/profile/issuer/hub identity/environment values vào continuation object. Policy hiện cố định `sol_xhigh / continuation_proposal / controller_required`. Outer route/mode nếu required phải theo validated current flow, không suy rằng `mcp_only/deterministic` của RUN recovery là route cho model continuation. Không dùng field `solution_shadow`; public field đã expose là `solution_shadow_recommendation`, và chỉ gửi khi workflow thật sự cần.

### 6.3. Consent và start

Nếu nhận `RUN_CONTINUATION_CONSENT_REQUIRED`, lấy **nguyên** `details.user_command`:

```text
/coding-tools-continue-consent <descriptor nguyên văn do runtime phát sinh>
```

Người dùng gửi qua host hỗ trợ; AI không tự gửi thay để giả consent. Sau khi host ghi nhận đúng receipt, retry cùng scoped request có exact RUN/WAVE. Nếu response báo scope/epoch/context đổi, dựng lại preflight hợp lệ; không tự sửa descriptor cũ. `GRANTED` chưa nghĩa đã start.

```json
{"action":"run_continuation","run_continuation_action":"start","run_id":"<RUN_ID>","task_context_id":"<CURRENT_CONTEXT_ID>"}
```

Sau start: giữ autonomous window ở G2; không poll `observe`. Nếu response là durable operation, đọc operation/Job qua cơ chế observation đã kiểm tra không dispatch lại; không gọi start lần hai vì thiếu output.

### 6.4. Pause/recovery, chỉ khi có nguyên nhân và authority

```json
{"action":"run_continuation","run_continuation_action":"pause","run_id":"<RUN_ID>","continuation_reason":"<EXACT_REASON>","task_context_id":"<CURRENT_CONTEXT_ID>"}
```

`reconcile`, `resume`, `revoke` có cùng outer action và exact RUN. Không trình bày ba action này thành chuỗi luôn phải chạy: chọn theo state/effect/Job và quyền hiện hành. `resume → start` chỉ khi grant còn hợp lệ, chưa revoke, pending state đã giải quyết; epoch/contract thay có thể đòi legal regrant.

### 6.5. Acceptance và completion report ACK

```json
{"action":"accept","run_id":"<RUN_ID>","wave_id":"<CURRENT_ACCEPTING_WAVE_ID>","task_context_id":"<CURRENT_CONTEXT_ID>"}
```

Đây là shape tối thiểu; nếu natural `full_problem` claim hoặc source adoption cần coverage/acceptance_files, phải đáp ứng đúng runtime guard, không copy exemptions của no-patch recovery. Acceptance không hợp lệ thì giữ lỗi, không đổi claim để lách.

Sau accept, dùng exact `get`, trình bày current report; chỉ ACK khi binding rõ và chưa ACK:

```json
{"action":"ack","run_id":"<RUN_ID>","message_id":"<CURRENT_COMPLETION_REPORT_ID>","task_context_id":"<CURRENT_CONTEXT_ID>"}
```

`accepted_or_not=ACCEPTED` có thể đi cùng report đang chờ **acknowledgement**; không chờ nó thành `PENDING_FINAL_ACCEPTANCE`. Không gửi `report_id` thay `message_id`. Không ACK report cũ của RUN khác.

## 7. Validation và phép đọc sẵn có

**Các lệnh trong mục này là lệnh đề xuất cho AI triển khai, chưa được chạy như test trong lần lập kế hoạch.** Chọn lane theo delta; không chạy tất cả một cách máy móc.

### 7.1. Baseline read-only

Tại `E:\DEV\Codex-web`:

```powershell
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short
git log -3 --oneline
npm run dev:status
python resources/coding-tools-mcp/scripts/report_lifecycle_census.py --workspace E:\DEV\Codex-web
```

Census chứa nhiều RUN; lọc kết quả trong memory để đọc summary và exact targets, không hạ stale threshold cho tiện. Census query-only không cấp phép reconcile. Không gọi nhiều reporter SQLite nặng song song.

### 7.2. Khi sửa Python continuation/bridge/authority

Working directory phải là `E:\DEV\Codex-web\resources\coding-tools-mcp`:

```powershell
python -m pytest tests/test_run_continuation.py tests/test_codex_bridge.py -q
python scripts/check_module_size.py
```

Đây là affected-subsystem lane, không phải mặc định mỗi lần sửa một dòng. Bắt đầu bằng node ID liên quan sau khi kiểm tra `rg '^class '` / `rg 'def test_'`. Nếu sửa consent/host correlation, thêm test đúng module/Node journal; nếu sửa knowledge reattach, thêm focused `tests/test_controller_continuity.py`. Chỉ rerun phần cần để chứng minh source cuối.

Các selector đã xác minh tồn tại trong source snapshot, để AI không phải tìm lại toàn bộ suite:

| File / class | Test tiêu biểu | Giới hạn bằng chứng |
|---|---|---|
| `tests/test_run_continuation.py::RunContinuationSurfaceTests` | `test_failed_proof_dispatches_one_bounded_repair_turn_then_reaches_accepting` | Có local proof command, model/bridge giả lập; không phải provider live |
| Cùng file/class | `test_patch_proposal_journals_backup_runs_structured_proof_and_stops_at_accepting` | Exact patch/backup/proof/acceptance barrier |
| Cùng file/class | `test_lost_bridge_ownership_pauses_instead_of_starting_a_duplicate_turn` | Lost ownership phải pause |
| Cùng file/class | `test_persistent_lane_recovery_restores_exact_session_before_one_new_turn` | Exact session recovery với bridge giả lập |
| Cùng file/class | `test_persistent_lane_recovery_rejects_missing_consent_or_stale_epoch_without_dispatch` | Thiếu consent/epoch sai không được dispatch |
| Cùng file/class | `test_restart_with_pending_dispatch_pauses_without_restoring_or_replaying` | Unknown pending action không replay |
| `tests/test_codex_bridge.py::CodexBridgeTests` | `test_persistent_restore_reclaims_the_registered_lane_without_turn_start` | Restore không tự start một lượt mới |
| Cùng file/class | `test_persistent_resume_rejects_workspace_or_session_mismatch` | Mismatch workspace/session bị chặn |

Ví dụ hai focused test cho một delta chỉ chạm recovery:

```powershell
python -m pytest tests/test_run_continuation.py::RunContinuationSurfaceTests::test_persistent_lane_recovery_rejects_missing_consent_or_stale_epoch_without_dispatch tests/test_run_continuation.py::RunContinuationSurfaceTests::test_restart_with_pending_dispatch_pauses_without_restoring_or_replaying -q
```

Nếu delta chạm host turn-end observer, tại repo root:

```powershell
node --test --test-name-pattern="observer finalizes turn features at turn end|observer emits a larger final structural snapshot" tests/chat-evaluation-journal.test.js
```

Các Node observer tests dùng VM/fake DOM/clock, không thay cho actual browser stream/detach proof. Negative-capability, concurrent fencing và budget tests chọn thêm từ đúng hiện hành khi surface đó thay đổi; không biến bảng ví dụ thành danh sách đủ cho mọi loại patch.

Compile/syntax check và `git diff --check -- <EXACT_CHANGED_PATHS>` chọn theo file thực sự thay đổi. Không tăng module-size allowance hoặc nới validator chỉ để xanh.

### 7.3. Báo cáo natural cross-session

Tại repo root, sau khi receipts đã tồn tại:

```text
python resources/coding-tools-mcp/scripts/report_cross_session_continuity.py --workspace E:\DEV\Codex-web --problem-id <EXACT_PROBLEM_ID> --problem-revision <EXACT_INTEGER_REVISION>
```

Reporter không tạo Session A/B, reattach, outcome hay autonomy. Đọc mọi `INCOMPLETE/UNAVAILABLE/FACT_WINDOW_TRUNCATED`; thiếu receipt thì thiếu proof, không điền tay. Báo cáo TG6 có thể đòi scope rộng hơn test driver thuần, nên ghi riêng gate nào đang đánh giá.

### 7.4. Khi bàn giao package được phép

Theo `package.json` snapshot, `npm run dist` đã bao gồm `test:all`. Không vừa chạy automatic `verify:all` root vừa lặp `dist` trong canary như một cách “chắc hơn”. Lập một package lane ngân sách riêng; theo dõi process thật đến terminal, validate artifact SHA và relevant smoke. Khi timeout, phân biệt outer workflow deadline, inner Job timeout và failure trong code.

## 8. Ma trận lỗi → hành động hữu hạn

| Quan sát | Hành động đúng | Không làm |
|---|---|---|
| Schema reject thêm field | So current schema, sửa payload tối thiểu nếu quyền/yêu cầu cho phép; ghi deviation | Gửi nguyên lỗi lặp lại hoặc loosen additionalProperties |
| Consent missing | Hiển thị exact runtime-issued command cho người dùng | Fake host receipt/generic ACK |
| Context/Problem/authority sai | Đọc exact binding và legal reattach; giữ BLOCKED nếu chưa có | Ghép Continuity Core của Problem khác |
| Provider auth/profile chưa dùng được | Báo đúng layer, thực hiện tối đa một retry nếu transient và evidence mới | Đổi model, custom argv, mở shell/network |
| Check fail trong scope | Typed REPLAN + bounded repair cùng RUN | Chạy release/package hoặc mở task mới |
| Budget hết | Pause có reason, giữ partial receipts; xin quyết định ngân sách nếu cần | Auto reset counters hoặc regrant vô hạn |
| Mixed/unknown effect | Stop dispatch; exact reconcile qua controller | Replay patch/command, sửa DB hoặc xóa evidence |
| Foreign live writer | Không ghi; giao đúng owner hoặc dùng scope cô lập được cấp quyền | Force release/kill/overwrite |
| Stale candidate không live owner | Classify; official exact-ID preflight chỉ khi thực sự cần và được phép | Bulk cleanup/stop tất cả active RUN |
| Report nested trước accept còn cũ | Đọc current exact state, phân biệt snapshot với latest report | Accept lại hoặc ACK nhầm |
| Source/runtime changed | Invalidate proof/gate bị ảnh hưởng; controlled activation khi được phép | Reuse một PASS toàn hệ thống cũ |

Tối đa một retry transport tạm thời nếu kết quả effect đã biết; unknown dispatch thì reconcile, không retry mù. Hai lần cùng lỗi không có bằng chứng/chiến lược mới: dừng nhánh, báo causal blocker và next action cụ thể; không tạo chuỗi RUN để che thất bại.

## 9. Bằng chứng cần nộp và bảng đóng mục tiêu

Dùng ledger/report sinh bởi runtime cho authority; tài liệu này chỉ là bản đồ. Nếu cần artifact tổng hợp, mở rộng reporter hiện có hoặc ghi summary gắn snapshot; không tạo database/sổ authority thứ hai. Không persist private reasoning, secrets hay full transcript.

Mỗi gate ghi:

```text
Gate ID / PASS | FAIL | INCOMPLETE | NOT_APPLICABLE
Observed time + source HEAD + source/worktree fingerprint
Endpoint/workspace/process/server/epoch identity
Problem ID/revision + RUN/WAVE + policy/generation (nếu có)
Exact commands actually run + cwd + exit/timeout
Proof IDs + input hashes + action/Job/thread/turn identity
Host t0 + subsequent event sequence + external-control-call classification
Source files changed/adopted + protected-oracle hash comparison
Controller receipt / checkpoint / current report ACK
Remaining work + exact next action + authority needed
```

Trường chưa có phải `unknown/unavailable`, không lấy epoch trước, không thay bằng chuỗi có vẻ hợp lệ. Provider cost chưa expose thì để unknown, không lấy internal credits làm hóa đơn. Tách thời gian driver làm việc, chờ provider/test và chờ người dùng consent/acceptance.

### Definition of done của C

- [ ] Baseline/target/authority đúng và không foreign writer.
- [ ] Live proposal path đạt trên đúng identity hoặc exact reusable receipt.
- [ ] Có action mới sau host t0 trong cửa sổ không external stimulation.
- [ ] Repair branch được chứng minh; first-pass/controlled/natural phân biệt rõ.
- [ ] Scope/protected oracle/budget/expiry/revoke/late-generation guards đạt.
- [ ] Reconnect/unknown-effect/restart boundary đạt đúng contract v1; không false auto-recovery claim.
- [ ] Natural task có independent confirmed outcome; nếu reopen thì goal sửa lỗi vẫn mở.
- [ ] Current candidate có controller acceptance, checkpoint và đúng report ACK.
- [ ] Không còn Job/write lease/unresolved own effect của packet; foreign state được báo riêng.
- [ ] Operator đã nhận checkpoint cuối gồm what changed/proof/remaining/next action.

Chỉ khi mọi mục bắt buộc có evidence mới được ghi **CLOSED_CONTINUATION_V1** trong báo cáo con người; đây không phải tên enum mới để ghi vào runtime. `INCOMPLETE` hoặc safe blocked không phải complete.

## 10. Các nhánh còn lại nếu muốn đóng rộng hơn

| Nhánh | Khi nào cần | Tiêu chí đóng | Không cản C khi |
|---|---|---|---|
| Strict rediscovery | Breaking contract hoặc release requirement chỉ định strict | Real current-client tools/list hoặc server/discover + process/epoch/SHA/timestamp + guarded official ACK | Compatible contract được runtime chấp nhận và task không yêu cầu strict |
| Historical RUN hygiene | Exact candidate cản lifecycle/delivery hoặc người dùng giao reconcile | Official exact-ID preflight, đúng authority/quiescence, no evidence loss, postflight integrity | Chỉ là inactive threshold candidate, không ownership/effect cản packet |
| 5–10 natural tasks và economics | Đánh giá hiệu quả/vận hành đại diện | Cohort thật, lỗi/blocked giữ denominator, coverage/rework/time/cost có provenance | Chỉ đóng chức năng v1, chưa claim hiệu quả thống kê |
| UI/operator usability | UI che trạng thái/thiếu thao tác cần thiết | Hiển thị đúng đang chạy/chờ user/ngân sách/accepting/terminal, một flow dùng thật | Chỉ còn thẩm mỹ không ảnh hưởng sử dụng |
| Independent-machine + upgrade/rollback | Sẵn sàng phân phối | Exact artifact trên máy độc lập, data/identity/rollback preserved, consent target rõ | Chỉ bàn giao source/local candidate |
| Publish/deploy | Người dùng nêu đích và hành động | Version/artifact/hash/changelog/target/rollback verified | Chưa được yêu cầu; tuyệt đối không tự phát hành |

Không dùng các nhánh rộng này để giữ mục tiêu C mở vô hạn. Ngược lại, C-closed không được dùng để tuyên bố toàn hệ thống/release/production đã hoàn thiện.

## 11. Prompt tổng để giao AI triển khai

Copy nguyên đoạn dưới và đính kèm tài liệu này. **Đoạn mẫu không tự cấp quyền trong phiên đang lập kế hoạch.** Người giao việc cần xác nhận phạm vi thực thi/chi phí/service tương ứng; consent descriptor vẫn do runtime phát sinh.

```text
Bạn tiếp quản việc hoàn thiện Durable RUN Continuation tại E:\DEV\Codex-web.
Đọc AGENTS.md và docs/CONTINUATION_CLOSURE_PLAN.md đầy đủ. Đây là kế hoạch
nguồn; mọi identity/status phải xác minh lại, không biến snapshot thành quyền.

Mục tiêu: hoàn thành H0 nếu source/runtime chưa có fallback authority, sau đó đóng
C (G0–G5) bằng bằng chứng thực tế rằng MCP tự tiếp tục công việc
kỹ thuật trong grant sau khi lượt ChatGPT kết thúc, có repair/stop/recovery
đúng contract và kết quả natural được nghiệm thu. Không tự thu hẹp mục tiêu
thành npm dev:status, test pass, ACK hoặc chỉ source presence.

Ưu tiên dùng run_continuation + existing App Server proposal bridge. Không
thêm Goal Engine/database/router/public tool. Không mở lại C4 306c...;
không redo packet 19 file hoặc recovery đã accepted nếu exact receipt còn khớp.
Phân loại riêng RUN Control Center 4af4... đang chờ acceptance; không tự nhận
ownership/accept nó từ global projection.

H0 trước G0: tái hiện `PRL_HOST_IDENTITY_UNAVAILABLE` ở public Problem path và
chỉ sửa asymmetry Electron receipt/attested ChatWeb transport tại hai path đã
chỉ định trong §0. Không fabricate/restore pending receipt. Proof H0-source
không phải live continuation proof; phải controlled activation rồi mới retry
đúng một lần public `problem.open` từ context ChatWeb hiện hành.

G0 tiếp theo: xác minh root/HEAD/dirty WIP, accepted bytes, runtime/process/epoch,
Coding-VP Live binding, controller/Problem Revision, public schema, active jobs
và write owner. Giữ tất cả WIP/.coding-tools. Chỉ sửa defect đã tái hiện trong
allowlist và đúng lease; chọn smallest focused oracle và proof fingerprint.

Được chủ động phân tích, chuẩn bị packet/fixtures và chạy kiểm chứng trong
phạm vi tôi thực sự đã cho phép. Nếu provider cost, source write, UI detach,
isolated service operation hoặc commit/package cần quyền chưa có, nêu đúng
target/scope/budget và xin đúng quyết định thiếu; không hỏi lại quyền chung.
Khi runtime đòi one-shot consent, trả nguyên details.user_command để tôi gửi
qua host. Không tự giả user command/host receipt/copy hub_client/direct SQLite.

Trong autonomy window sau host t0: không prompt “tiếp tục”, không public
run_continuation observe/start/resume/reconcile. Chỉ passive evidence reader;
chứng minh action mới sau t0 do MCP worker. Nếu measurement bị can thiệp,
không công nhận PASS. Không sửa protected tests để lấy xanh.

Giữ budget <=900s/12 turns/3 patch attempts. Phân biệt resume→start, stale
epoch needing consent, unknown effect needing reconcile, và ACCEPTING needing
controller review. Giữ RUN qua technical REPLAN, không tạo RUN mới để che lỗi.

Sau mỗi gate, báo what changed/current state/proof/failure/remaining/next
action; tiếp tục bước hợp lệ kế tiếp, không dừng vô cớ sau tool result. Dừng
chỉ ở exact authority/semantic blocker hoặc khi definition of done đã đủ.
Không push/tag/publish/deploy/restart live/commit/package nếu chưa có yêu cầu
và target rõ. Handover cuối phải tách C/D/E, liệt kê unproven gates trung thực.
```

## 12. Prompt ngắn theo packet

### Packet H0 — Sửa authority asymmetry trước khi tạo Problem

```text
Thực hiện duy nhất H0 trong docs/CONTINUATION_CLOSURE_PLAN.md. Tái hiện bằng
focused test rằng attested ChatWeb controller với W3C trace, không có Electron
pending receipt, hiện không mở được Problem vì PRL chỉ gọi
claim_pending_host_turn(). Chỉ sửa problem_lineage_control.py và
tests/test_problem_lineage.py: prefer Electron claim; when absent, use existing
_attested_chatweb_transport_turn(); preserve mismatch and no-authority failure.
Không tạo/restore pending receipt, không trust caller turn/trace, không đổi
public schema/provider/route/sandbox/budget, không chạm .coding-tools hoặc
concurrent WIP. Run exact focused tests and report diff/proof. Sau source proof,
dừng trước activation/live retry và nêu exact lifecycle target/authority needed.
```

### Packet P0 — Audit/đóng authority gap, không chạy inference

```text
Thực hiện G0 của docs/CONTINUATION_CLOSURE_PLAN.md theo chế độ read-only trước.
Trả MATCH/DRIFT/UNKNOWN cho baseline, exact runtime/context, RUN own vs foreign,
schema capability, check definition và điều kiện consent. Không tạo RUN hay
grant đến khi thật sự cần cho canary và có scope/authority; không ACK/accept
RUN khác. Chốt một natural candidate có repro hoặc nói rõ hiện chỉ có fixture.
```

### Packet P1 — Canary live và detached autonomy

```text
Thực hiện G1/G2 trong scope đã được phê duyệt. Reuse canary nếu exact proof
còn khớp; nếu không, một live bounded proposal qua current compatibility path.
Ghi host t0, dừng external stimulation và thu passive receipts. Return timeline,
action/Job/proof IDs, oracle hashes, mode/model thực sự quan sát, PASS/INCOMPLETE.
Không coi public observe polling là bằng chứng tự chạy; không sửa source ngoài
candidate allowlist; không self-accept.
```

### Packet P2 — Repair/fault matrix cô lập

```text
Thực hiện G3/G4 bằng focused tests và isolated harness đã được phép. Bảo vệ
oracle; tách fake/controlled/live/natural. Kiểm tra fail→repair, revoked/expired,
late-generation, exact persistent session, pending dispatch/Job và mixed effect.
Không fault-inject runtime live. Không bỏ epoch/consent guard. Chỉ patch module
có failing oracle cụ thể, chứng minh fix rồi review hậu điều kiện safe stop.
```

### Packet P3 — Natural acceptance và bàn giao

```text
Thực hiện G5, sau đó G6 chỉ với quyền bàn giao đã có. Không dùng synthetic
fixture làm natural outcome, không dùng accepted code làm independent outcome.
Đối chiếu exact criteria/proof/bytes, controller accept, current report get/ACK,
reporter exact revision và job/lease/effect quiescence. Cập nhật maintained docs
đúng delta; không rewrite research lịch sử. Kết luận C/D/E riêng, chưa có bằng
chứng thì ghi INCOMPLETE/NOT_AUTHORIZED, không nói toàn dự án đã hoàn thiện.
```

### Mẫu người dùng phê duyệt một canary cụ thể

Đây là mẫu để người dùng đọc, điền và gửi cho AI; không phải consent đã được phát sinh:

```text
Tôi cho phép thực hiện canary continuation [CASE_ID] trên Coding-VP Live tại
E:\DEV\Codex-web, chỉ đọc [READ_PATHS], chỉ sửa [WRITE_PATHS], không sửa
[PROTECTED_TEST_PATHS]. Oracle/checks là [EXACT_ARGV_AND_CWD].
Tôi cho phép App Server proposal qua profile continuation_proposal của dự án,
tối đa [SECONDS <= 900], [DECISION_TURNS <= 12], [PATCH_ATTEMPTS <= 3].
Cho phép kết thúc lượt chat/đóng đúng view của canary để kiểm chứng driver;
không dừng Recovery Host/MCP/Tunnel live, không đóng các task khác.
Không commit/push/package/publish/deploy, không tăng ngân sách, không thêm
provider/model hoặc thay sandbox. Nếu một bước cần isolated process fault,
hãy nêu riêng exact fixture/runtime/PID owner và chờ tôi cho phép bước đó.
Hãy đưa nguyên one-shot consent command runtime trả ra để tôi gửi qua đúng
host. Sau consent, làm tới kết quả kiểm chứng hoặc blocker cụ thể và báo cáo.
```

Không gửi mẫu còn placeholder. Một consent hợp lệ có scope đã thay đổi không được tái dùng cho case khác. Controller nghiệm thu sau cùng vẫn theo policy hiện hành; canary authorization không cấp cho model proposal quyền tự accept.

## 13. Nguồn để AI tự đối chiếu

Paths trong mục này là repo-relative; root đầy đủ là `E:\DEV\Codex-web`. Line numbers có thể đổi, tìm lại symbol khi implementation đổi.

- `docs/CURRENT_STATE.md` §0 và contract tại dòng 231: convergence, evidence ladder, compatible vs strict.
- `resources/coding-tools-mcp/coding_tools_mcp/continuation_driver.py`: `_run_continuation_start_worker`, `_run_continuation_observe_driver`, `_run_continuation_dispatch_repair`, `observe_continuation_effect`, `mark_accepting`.
- `resources/coding-tools-mcp/coding_tools_mcp/run_continuation.py`: `_run_continuation_grant`, `_run_continuation_start_driver`, `_run_continuation_control`, effect reconciliation và generation/fencing.
- `resources/coding-tools-mcp/coding_tools_mcp/continuation_contract.py`: current proposal schema, budgets, `_normalize_check`, `continuation_consent_descriptor`.
- `resources/coding-tools-mcp/coding_tools_mcp/codex_bridge.py` và `app_server_persistence.py`: fixed profile, exact launch/session/turn recovery; không suy từ config ra provider proof.
- `resources/coding-tools-mcp/coding_tools_mcp/tool_schema.py`: public field/enum hiện có; client expose mới là invocability thực tế.
- `electron/services/chatEvaluationJournal.js` và `coding_tools_mcp/host_correlation.py` trong MCP package: observed user consent và host-turn correlation.
- `resources/coding-tools-mcp/scripts/report_lifecycle_census.py`, `report_cross_session_continuity.py` và corresponding report modules: query-only evidence và missing gates.
- `docs/research/260907_DURABLE_RUN_CONTINUATION_IMPLEMENTATION_PROGRESS.md`, `260907_RUN_CONTINUATION_APP_SERVER_COMPATIBILITY_FINDING.md`: lịch sử implementation/proof/provider finding, không override current code.
- `.coding-tools/orchestration/reports/run-ad6202865db749d9b0155ffc32bf5dd9/run-summary.md`, `run-ed5230994c074466b1d21bf0eb0a2d23/run-summary.md`, `run-4af4b6a6240d4207b2fea6b9fe169d7f/run-summary.md`: generated ledger views đã đọc khi lập kế hoạch.
- `docs/TESTING.md`, `docs/RELEASE_CHECKLIST.md`, `package.json` và `AGENTS.md`: scope validation/delivery. Khi guidance stale, implementation/test hiện hành có ưu tiên theo repo policy.

**Quy tắc cuối:** hoàn tất là một kết quả có thể kiểm chứng với ranh giới rõ, không phải số lần tool đã chạy, số report đã ACK hay số lớp kiến trúc đã thêm.
