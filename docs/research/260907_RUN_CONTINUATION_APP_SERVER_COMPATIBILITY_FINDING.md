# Tương thích App Server cho `run_continuation`

> **Quan sát:** 2026-09-07 (Asia/Ho_Chi_Minh)
> **Phạm vi:** adapter proposal no-tools của `run_continuation`; đây là một
> finding vận hành/source có thời điểm, không thay thế checkpoint EOCL, strict
> connector discovery, natural Problem outcome, hay release proof.

## Kết luận

App Server cục bộ của phiên quan sát không hoàn tất một turn
`continuation_proposal` khi bridge gửi trường `outputSchema`, cả với schema
canonical có `oneOf` lẫn envelope object không dùng `oneOf`. Cùng profile,
model, prompt vô hại và sandbox, turn hoàn tất khi không gửi trường đó.

Vì vậy adapter không còn yêu cầu provider enforced structured output. Thay vào
đó, prompt mang một response contract JSON rõ ràng và MCP vẫn là validation
boundary duy nhất: `parse_run_continuation_proposal()` phải decode/kiểm tra toàn
bộ object trước khi đề xuất có thể thành READ, PATCH, Job hay proof. Không có
redaction, extraction từ prose, auto-correction hay write fallback.

Đây là thay đổi compatibility nhỏ hơn việc đổi model, thay route, cho model
quyền tool, hoặc nới parser. Route tiếp tục cố định là `gpt-5.6-sol/xhigh`; App
Server turn vẫn `approvalPolicy=never`, sandbox `readOnly`, network `false`,
shell/multi-agent bị tắt. Model không sở hữu workspace write, command, browser,
network, Job, proof, acceptance hay continuation grant.

## Phép phân biệt đã chạy

Tất cả prompt canary dưới đây là content-free, không gửi file nguồn, credential,
Problem thật, RUN thật hay patch. Các sidecar thread là ephemeral và bị đóng sau
quan sát.

| Cấu hình | Kết quả quan sát | Diễn giải |
| --- | --- | --- |
| `continuation_proposal` + canonical `RUN_CONTINUATION_PROPOSAL_SCHEMA` | terminal `failed`, không có agent text | App Server profile không dùng được structured-output này. |
| `continuation_proposal` + object envelope không `oneOf` | terminal `failed`, không có agent text | Không chỉ riêng `oneOf`; `outputSchema` là incompatibility tại runtime quan sát. |
| Cùng profile, không `outputSchema`, prompt `READY` tối giản | terminal `completed`, text `READY` | Model/profile/sandbox/provider lane hoạt động khi bỏ structured output. |
| Source prompt mới, không `outputSchema` | terminal `completed`; JSON object `BLOCKED`; strict parser pass, evidence hash match | Contract trong prompt và parser fail-closed chạy đúng ở provider boundary. |

Không in text proposal hoặc data provider ngoài metadata tối thiểu trên. Hai
preflight fixture sai (`approved_checks` rỗng, sau đó `cwd="."`) bị policy từ
chối trước khi dispatch model; chúng không phải provider canary và không làm
nới contract để test đi qua.

## Mặt source thay đổi

- `coding_tools_mcp/codex_bridge.py`: profile yêu cầu một JSON object theo
  response contract trong prompt; không diễn đạt output schema là bắt buộc.
- `coding_tools_mcp/run_continuation.py`: packet nêu exact JSON response
  encoding/variant/field rules; initial proposal dispatch không gửi
  `outputSchema`.
- `coding_tools_mcp/continuation_driver.py`: READ follow-up và technical repair
  follow-up cũng không gửi `outputSchema`, nên không có một path resume bị lỗi
  khác initial turn.
- `tests/test_codex_bridge.py` và `tests/test_run_continuation.py`: regression
  proof cho omission wire field, prompt contract, và strict local parse failure.

`RUN_CONTINUATION_PROPOSAL_SCHEMA` vẫn được giữ là mô tả canonical của proposal
và parser vẫn kiểm tra chặt từng variant. Omission ở wire transport không làm
schema hoặc validation trở thành advisory.

## Bằng chứng hiện có và phần chưa được suy ra

- Focused source/bridge/transport proof sau sửa phải được chạy và ghi riêng;
  canary này không thay thế unit/contract proof.
- Runtime được full-clean refresh trước finding này; một sửa source sau refresh
  tạo `mcp_update_pending` mới cho đến refresh/activation tiếp theo. Không gọi
  runtime cũ là đã nạp adapter mới.
- Không có strict `tools/list`/`server/discover` từ connected ChatWeb client,
  official Recovery Host connector acknowledgement, exact EOCL accepted
  checkpoint, granted natural RUN, UI detach proof, restart/fault matrix,
  package, release, deploy hay production outcome trong finding này.
- Vì không có current authenticated ChatWeb controller, canary không gọi
  `task_control/run_continuation`, không tạo grant, không chạy Job/PATCH/proof,
  và không tự nhận final acceptance.

## Hành động tiếp theo

1. Re-run affected source proof and commit the exact adapter/test/document
   packet through the repository delivery guard.
2. Controlled full-clean refresh the final source, then require a fresh real
   `tools/list` or `server/discover` receipt and official Recovery Host ACK.
3. Chỉ sau exact controller grant mới chạy natural bounded continuation,
   controller review/accept-or-reject, UI detach, và restart/fault matrix.
