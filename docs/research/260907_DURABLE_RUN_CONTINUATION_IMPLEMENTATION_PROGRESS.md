# Tiến độ triển khai `run_continuation`

> **Cập nhật:** 2026-09-07 (Asia/Ho_Chi_Minh)
> **Cơ sở thiết kế:** [Quyết định RUN chủ động gọi model](260907_DURABLE_RUN_CONTINUATION_IMPLEMENTATION_DECISION.md)
> **Phạm vi:** tài liệu này ghi mức bằng chứng của checkout đang làm việc; không viết lại các kết luận nghiên cứu lịch sử thành kết quả runtime.

## Kết luận triển khai tại source checkpoint hiện hành

Phần lõi của tư vấn đã được hiện thực ở mức **`SOURCE_PRESENT + FOCUSED_PROOF`**: một RUN được cấp grant có hạn nay có thể tự điều phối một lane proposal App Server đã được cố định, thực hiện vòng `READ → proposal tiếp` hoặc `PATCH → journal → exact patch → structured proof → ACCEPTING` mà không dùng lại `hub_client` của ChatWeb trong worker.

Điểm quan trọng không phải là thêm một background thread. Driver mới giữ nguyên authority của hệ thống hiện hữu:

```text
ChatWeb/Sol: cấp contract, grant, pause/revoke và final accept/reject
        ↓
RUN/WAVE + canonical ledger: generation, action/evidence cursor, effect/Job receipt
        ↓
MCP continuation driver: sole writer, proof broker, fail-closed recovery
        ↓
Codex App Server: fixed no-tools proposal generator, không có write/shell/network/delegation authority
```

`ACCEPTING` vẫn chỉ là kết quả kỹ thuật đủ bằng chứng để ChatWeb/Sol review. Driver không checkpoint RUN, không tự kết luận Problem/business outcome, không commit, push, restart, publish, deploy hoặc mở rộng scope/budget.

## Những phần đã thay đổi

| Bề mặt | Hiện thực đã có | Invariant được giữ |
| --- | --- | --- |
| `coding_tools_mcp/run_continuation.py` | Grant bất biến, CAS generation, action/evidence cursor, persistent thread/turn identity, check-Job pointer và `run_continuation_effects` trong canonical ledger | Không tạo DB, Goal/Task/Attempt hay public MCP tool mới; RUN/WAVE vẫn là state machine duy nhất. |
| `coding_tools_mcp/codex_bridge.py` | Profile `continuation_proposal` cố định `gpt-5.6-sol`/`xhigh`, read-only, no-network, approval never, shell/multi-agent/browser/app/plugin/memory disable; custom Codex argv bị reject | Model chỉ tạo typed proposal; boundary source này không được diễn đạt thành provider live proof. |
| `coding_tools_mcp/continuation_driver.py` | Worker không copy request/hub context; revalidate admitted runtime và RUN/WAVE/source trước dispatch/effect; exact turn observation; bounded READ cursor; effect journal/backup/reconcile; MCP-only patch, Job và proof route | Không resume/replay một turn hoặc effect không phân loại được; unknown chuyển pause/replan. |
| `coding_tools_mcp/file_tools.py` + `patching.py` | Reuse exact preimage/postimage writer và existing atomic in-process committer; driver materialize retained preimages trước mutation | Backup chỉ được ghi trong `.coding-tools/orchestration/continuation-effects/<action-id>/`; không mở quyền generic vào `.coding-tools`. |
| `coding_tools_mcp/exec_tools.py` + `landlock_exec.py` | Internal continuation proof chỉ nhận exact `argv`, `shell=False`; Landlock helper có structured-argv path, không chuyển argv thành shell text | Không public escape hatch; network/destructive/sensitive-env posture vẫn được kiểm tra, Job vẫn do execution governor sở hữu. |
| `tool_schema.py` | Vẫn chỉ tám public MCP tools. `task_control/run_continuation` có `get`, `start`, `observe`, `reconcile`, `pause`, `resume`, `revoke` | `observe` không cấp quyền; `reconcile`, pause/resume/revoke và start đều bị gate đúng mức. |
| `tests/test_run_continuation.py` + `tests/test_landlock_exec.py` | Focused contract, legacy migration, READ driver, effect, no-shell/Landlock và integrated local packet proof | Test fixture/provider giả không được báo là browser-loss hoặc App Server canary thật. |

## Hợp đồng và vòng thi hành hiện có

### 1. Grant chỉ cấp một packet kỹ thuật đã xác định

Grant vẫn chỉ hợp lệ với `agent_workflow` `phase=prepare`, `bugfix`/`feature`, exact Problem Revision/RUN/workspace/contract/tool-contract/runtime behavior, admitted runtime và attested active ChatWeb controller. Nó cố định route/profile, `read_paths`, `write_paths`, protected paths, tối đa 15 phút / 12 decision turns / 3 patch attempts, và check definition gồm `argv`, `cwd`, `environment_hash`, `definition_hash`.

Khi cấp, mỗi check phải bind đúng `continuation_execution_environment_hash` hiện hành. `task_control/run_continuation/get` trả hash content-free này để caller không tự đoán environment. Mismatch environment trước proof là drift/replan, không phải lý do lặng lẽ chạy trên máy khác.

### 2. READ thực sự bounded, không phải action giả

Turn đầu nhận Problem capsule, source identity và catalogue `available_read_paths`, nhưng không nhận hết source bytes. `READ` chỉ có thể chọn path trong immutable allowlist. Driver persist `pending_evidence_paths_json`, dựng evidence hash mới, hoàn tất action cũ rồi append một turn mới trên **cùng exact bridge thread**. Vì evidence selection và hash là durable, response muộn hoặc read ngoài scope bị từ chối.

### 3. PATCH là write-ahead effect chứ không phải output model được áp thẳng

Với proposal `PATCH`, MCP tự làm theo thứ tự sau:

1. Rebuild evidence ở source hiện tại và so hash với action đang pending.
2. Derive exact postimage cho mỗi replacement/new file; old text phải match duy nhất.
3. Persist manifest pre/post hash vào `run_continuation_effects` **trước** filesystem effect.
4. Revalidate current RUN/WAVE/source identity trước khi journal hay materialize artifact; drift thì replan trước mutation/evidence effect mới.
5. Ghi/fdatasync retained backup hoặc absent-marker tại subtree chuyên dụng.
6. Acquire existing EOCL MCP write lease, kiểm tra exact scope/fence/source rồi gọi exact patch writer.
7. Reobservation mọi postimage; chỉ `all postimage` được ghi `applied`.
8. Chuyển sang `PROVING`, chạy chỉ các approved structured checks, và dùng existing managed Job + ProofLedger receipts.
9. Nếu proof xanh, MCP đưa wave đến `ACCEPTING`; ChatWeb/Sol vẫn phải `accept` hoặc `reject`.

`all preimage` sau crash được ghi `not_applied`; mixed/unknown được ghi `recovery_required`. Cả hai không reapply proposal cũ. Khi driver/bridge restart làm mất ownership của turn, trạng thái là `DISPATCH_UNKNOWN`, grant bị pause và action còn pending để buộc reconciliation có bằng chứng.

### 4. READY và BLOCKED không tạo bypass

`READY` không được model tự coi là thành công: MCP vẫn chạy toàn bộ approved proof, chỉ khi green mới tới `ACCEPTING`. `BLOCKED`, malformed JSON/schema, stale evidence, runtime behavior drift, lost bridge ownership, conflict preimage, check failure và effect recovery đều dừng bằng typed pause/replan; không có automatic model cascade, route escalation, new scope, raw shell hoặc retry mù.

## Bằng chứng source đã chạy

Focused test suite hiện bao phủ:

- grant replay/conflict, expiry/revoke, dual claim, generation/action fencing, scope/check deny, legacy in-place schema migration và fresh-ledger coverage;
- evidence cursor qua READ, terminal READ driver dispatch và second-turn identity trên cùng lane/thread;
- proposal stale/scope rejection, immutable effect manifest, terminal observation idempotency/conflict;
- backup materialization/reobservation, absent marker và retained original bytes;
- source/worktree drift ngay trước PATCH dừng tại `REPLAN_REQUIRED`, không tạo effect journal hay retained backup mới;
- provider/bridge ownership mất sau restart dẫn `DISPATCH_UNKNOWN + pause`, không dispatch turn thứ hai;
- structured proof argv bị từ chối nếu gọi từ public path, không chạy qua shell khi do internal driver gọi; Landlock JSON handoff giữ nguyên argv thay vì rơi về shell;
- packet local end-to-end: `PATCH → journal → retained backup → exact patch → managed structured proof → ACCEPTING`.

Các lệnh verification phải được đọc như source proof, không phải production proof:

```text
python -m py_compile coding_tools_mcp/run_continuation.py \
  coding_tools_mcp/continuation_driver.py coding_tools_mcp/codex_bridge.py \
  coding_tools_mcp/exec_tools.py coding_tools_mcp/landlock_exec.py coding_tools_mcp/server.py

python -m pytest tests/test_run_continuation.py tests/test_landlock_exec.py \
  tests/test_codex_bridge.py \
  tests/test_controller_continuity.py tests/test_orchestration_ledger.py \
  tests/test_orchestration_control.py tests/test_agent_workflow_idempotency.py -q

python scripts/check_module_size.py
git diff --check
```

Focused suite được recapture tại source checkpoint này: **99 passed, 5 subtests passed** trong 22.15 giây. Count này là bằng chứng source/focused proof của packet hiện hành, không phải bằng chứng App Server/provider, browser-loss hay production; diff review cũng được recapture sau mọi chỉnh sửa tiếp theo.

## Những ranh giới còn chưa được claim

| Gate | Trạng thái đúng |
| --- | --- |
| App Server/provider live call với profile `continuation_proposal` | **Chưa chạy.** Source/test xác nhận config và fake boundary, không chứng minh provider honors mọi capability flag. |
| Browser/UI close trong khi driver thực hiện natural RUN | **Chưa chạy.** Worker source không copy controller, nhưng chưa có controlled browser-loss canary. |
| MCP/Recovery Host restart giữa dispatch/effect/proof | **Chưa chạy real-process fault injection.** Code intentionally pauses unknown, không tuyên bố resume exactly-once. |
| Packaged Electron/activation/connector rediscovery | **Chưa kiểm chứng.** Không restart/activate service trong packet source này. |
| Natural bugfix, user acceptance, outcome/SLO | **Chưa có.** `ACCEPTING` không phải final user acceptance hay Problem resolved. |
| Commit/push/release/deploy | **Không thực hiện.** Dirty concurrent `.coding-tools` evidence và WIP vẫn được giữ nguyên. |

## Next gate có thẩm quyền riêng

Source implementation không tự cho phép canary. Nếu muốn tiếp tục từ đây, wave vận hành cần được authorize riêng để:

1. capture current runtime/connector/activation receipt và exact loaded revision;
2. run một App Server controlled no-tools negative-capability check, không lộ credentials;
3. chạy natural bounded bugfix trong allowed scope, đóng view UI (không stop runtime), thu canonical receipts và để RUN ở `ACCEPTING`;
4. test restart/recovery theo từng boundary, trong đó mixed effect phải giữ backup và pause;
5. ChatWeb/Sol review proof/diff rồi accept/reject; chỉ sau đó mới đánh giá package/release/pilot.

Không có bước nào ở trên được suy ra là đã được phê duyệt chỉ từ việc user yêu cầu triển khai source. Nếu sau này commit/push được yêu cầu, delivery phải tuân thủ `npm run stage:coding-tools-delivery` rồi `npm run check:coding-tools-delivery`, gồm canonical ledger và delivery snapshot nhưng không stage concurrent WIP không thuộc packet.

## Bổ sung source/proof — 2026-09-07 (không viết lại chronology ở trên)

Phần này thay thế các mô tả cũ trong tài liệu nếu chúng còn nói `CHECK_FAILED`
là terminal replan, model có thể chọn một tập proof con, claim chỉ được kiểm
tra bằng generation, hoặc reconciliation giữ pending action mãi mãi. Đây là
source và test trong worktree còn dirty, **không** là proof của provider,
browser, package hay runtime đã load.

1. **Proof coverage là bắt buộc.** Toàn bộ `approved_checks` của immutable
   grant là required coverage. `PATCH` có thiếu dù chỉ một hash bị deny bởi
   `RUN_CONTINUATION_REQUIRED_CHECK_MISSING`; `READY` vẫn chạy toàn bộ tập.
   Model không còn là bên quyết định đủ proof.
2. **PATCH budget có action receipt.** Ledger persist
   `pending_patch_action_id`; `consume_run_continuation_patch_attempt` trừ
   ngân sách trong transaction đúng một lần cho exact pending `action_id`.
   Replay cùng action là idempotent, action mới sau khi hết budget bị
   `RUN_CONTINUATION_PATCH_BUDGET_EXHAUSTED` trước effect journal.
3. **Claim là owner lease thực sự.** Mọi action/proof mutation cần exact
   `runtime_instance_id`, `driver_generation`, owner hiện tại và lease chưa
   hết hạn. Driver renew ở observation safe point và sau mỗi poll proof Job;
   owner khác hoặc claim quá hạn bị fence, không thể tiếp tục ghi cursor/job
   receipt.
4. **Failed proof tự technical-replan có giới hạn.** Sau patch sai/check fail,
   driver complete action cũ, record `CHECK_FAILED`, tạo WAVE mới trong cùng
   RUN từ post-effect source identity, persist bounded failed-proof context,
   rồi `continue_thread` trên exact thread. Scope, check set, duration,
   decision và PATCH budget không tăng. Nếu bridge/lease không còn exact thì
   pause/replan thay vì lặp mù.
5. **Pending effect có receipt recovery an toàn.** Reconciliation chỉ đi qua
   active authenticated controller, chỉ khi claim live đã pause/revoke/expired,
   exact effect đã được classify và Job còn pending đã được chứng minh terminal.
   Unknown dispatch hoặc Job còn live không bị clear. Khi terminalize được,
   cursor được đóng có event hash-chained; pause/resume hoặc revoke/regrant
   có thể đi tiếp ở WAVE mới mà không replay patch cũ.

Focused/inter-module source proof được recapture trên worktree hiện hành:

```text
python -m pytest tests/test_run_continuation.py tests/test_landlock_exec.py \
  tests/test_codex_bridge.py tests/test_controller_continuity.py \
  tests/test_orchestration_ledger.py tests/test_orchestration_control.py \
  tests/test_agent_workflow_idempotency.py -q

104 passed, 5 subtests passed in 26.59s

python scripts/check_module_size.py
module-size budgets ok
```

Trong đó `test_run_continuation.py` có direct regression cho: selected proof
subset bị reject; owner/renewal/expiry; atomic PATCH budget; controller
terminalization và regrant; và sequence fake bridge `wrong patch → failed
check → repair turn → correct patch → ACCEPTING`. Test này không gọi provider
thật, không đóng UI, không restart MCP/Recovery Host và không được dùng để
claim exactly-once qua real process restart.

Sau khi kiểm tra public transport schema, `test_mcp_sdk_smoke.py` cũng đã pass
`2 passed` qua MCP stdio thật của local test harness. Nó xác nhận surface vẫn
chỉ có tám tools và schema phát ra thực sự chứa đúng một action
`task_control/run_continuation` với bảy sub-action đã công bố. Đây vẫn chỉ là
source/transport-local proof: không tạo provider turn, không nạp runtime đang
chạy và không thay thế strict connector discovery.

## Bổ sung security boundary — evidence không được mang secret sang proposal model

Sau audit source, đường `read_files[].content` được xác định là một boundary
riêng: path nhạy cảm đã bị deny nhưng một path hợp lệ vẫn có thể chứa credential
literal. Từ checkpoint này, `_run_continuation_canonical_evidence()` fail closed
với `RUN_CONTINUATION_EVIDENCE_SENSITIVE` trước khi tạo prompt/bridge dispatch
nếu objective, Problem capsule, requested source content hoặc technical-replan
chứa sensitive-like assignment, Authorization Bearer/Token header hoặc private
key marker. Đây là detection boundary, không phải redaction: source bị sửa âm
thầm sẽ làm evidence hash không còn nghĩa và có thể khiến model patch sai
preimage. V1 giữ scope hẹp; controller có thể chọn một packet source an toàn
hoặc xử lý trực tiếp, nhưng driver không đưa material nghi ngờ sang provider.

Regression trực tiếp cover cả source file lẫn Problem capsule. Focused suite
được recapture sau thay đổi này, gồm MCP stdio schema smoke:

```text
python -m pytest tests/test_run_continuation.py tests/test_landlock_exec.py \
  tests/test_codex_bridge.py tests/test_mcp_sdk_smoke.py \
  tests/test_controller_continuity.py tests/test_orchestration_ledger.py \
  tests/test_orchestration_control.py tests/test_agent_workflow_idempotency.py -q

107 passed, 5 subtests passed in 28.81s

python -m compileall -q coding_tools_mcp/run_continuation.py \
  coding_tools_mcp/continuation_driver.py coding_tools_mcp/codex_bridge.py \
  coding_tools_mcp/exec_tools.py coding_tools_mcp/landlock_exec.py \
  coding_tools_mcp/server.py

python scripts/check_module_size.py
module-size budgets ok
```

Kết quả trên chỉ tăng proof cho byte source hiện hành. Nó không là proof provider
live, Browser/UI close, restart/recovery thật, connector receipt, package hay
production.
