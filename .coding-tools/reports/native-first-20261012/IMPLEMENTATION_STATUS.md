# Native-First Hybrid Agent — kết quả triển khai ngày 12-10-2026

## Kết quả và trạng thái vận hành

Đã triển khai source và chuẩn bị candidate Windows **native-first-1012-r5**.
Chưa kích hoạt native-first trên production và chưa hoàn tất canary live.
Người vận hành chọn giữ **Codex-web trước**, chờ xử lý UNKNOWN hợp lệ.

| Thành phần | Trạng thái mạnh nhất đã chứng minh |
|---|---|
| File API | Fixture đọc 100 file, exact PATCH 20 file + readback/hash đúng, không gọi runner/VM |
| Native router | Native-first/native-only/isolated; grammar Git/CLI, native prefix riêng; fail closed |
| Tiến trình native thực tế | 10 Node commands/10 terminal Jobs; Git helpers bị chặn; build Node được duyệt tạo đúng artifact |
| Tài nguyên/boundary | Job limits bắt buộc trước resume; path/network/cancel/auth focused proof đạt |
| VM lifecycle | Owned ID + lease generation + terminal Job gate + idle 30s; hai contention race đã sửa |
| Windows package r5 | Exact parity 89 app files/299 resources/9 adapters; isolated Recovery smoke đạt |
| Windows đang phục vụ | **r9e READY/OPEN**, policy/registry Autocad giữ nguyên; không kích hoạt r5 |
| Ubuntu prerequisite | Overlay 2 file được kiểm tra và archive tải lên; **chưa deploy** |
| Canary Codex-web | **Đang chờ**, shared principal chỉ có Autocad và unresolved-action guard chặn đổi pilot |

Public MCP facade schema **32**, tám tool smart-v3 và hash
`3664b70740d8d7359a3605b5ce42d7cbf3329e27dcfeec27d22b23ec9c631f66`
không đổi. Receipt mới bổ sung backend/isolation/policy vào hash; receipt cũ
vẫn giữ hợp đồng hash cũ.

## Thay đổi chính

- MCP core: `windows_execution_policy.py`; routing trong `exec_tools.py`,
  metadata trong Job/session; bắt buộc Windows Job RAM 2 GiB/64 process/CPU 50%;
  pinned MXC ProcessContainer, deny-path/no-DACL fallback/network deny.
- Lifecycle: `windows_mxc_state_aware.py`, terminal gate trong
  `session_control.py`; callback chờ khóa và deferred arm theo generation.
- Electron/UI: exec bridge, runtime orchestrator, enrollment, main forwarding,
  selector mode/consent gắn workspace/generation; metadata không warm-up VM.
- Control Plane: node agent, Recovery bridge, facade relay/hash/recovery.
  Diagnostic `TARGET_MISSING_BEFORE_DISPATCH` được tạo chỉ tại validation
  trước dispatch; generic missing/result failures vẫn UNKNOWN.
- Docs/scripts: `docs/NATIVE_FIRST_EXECUTION.md`, phần mới `CURRENT_STATE.md`,
  baseline observer, exact package verifier, prepared canary và guarded rollout.

Đã giữ nguyên các thay đổi dirty có từ trước. Không commit/push/amend/rebase.

## Bằng chứng kiểm tra

- Core native/security lane: **40 tests + 15 subtests** đạt; build fixture
  riêng đạt. `native-execution-final-proof.json` và
  `native-approved-build-proof.json` ghi process/Job/argv/hash thực tế.
- Idle/state-aware cuối: **46 tests + 21 subtests** đạt.
  `native-proof-source-freshness.json` xác nhận source native proof vẫn khớp.
- Control Plane metadata: focused JS/Python bridge/node/facade/contract đạt.
  **19 tests** đạt trên chính immutable Ubuntu overlay.
- UI/enrollment/workspace consent, file/runtime stop và Recovery focused lanes
  đạt; các lượt trùng nhau không được cộng thành tổng độc lập.
- r5 exact source/package parity và isolated packaged smoke đạt; **20** thế hệ
  tiến trình fixture quan sát được đã kết thúc, profile tạm đã dọn, descriptor
  production giữ nguyên.
- `git diff --check`, không unmerged entries, repository secret/history guard
  đạt. Full suite không được chạy vì focused proof đã bao phủ thay đổi.

## Hai gate còn lại

1. **Canary Codex-web:** ba UNKNOWN file-read actions của Autocad vẫn không có
   bằng chứng phân biệt lỗi trước/sau đọc. Diagnostic cũ có hai nguồn phát sinh;
   không được tự append rejected/completed receipt. Journal và receipt gốc giữ
   nguyên; không quarantine, replay, thay generation hoặc bypass authority.
2. **Ubuntu service transition:** read-only preflight trả
   `LIVE_WORK_BLOCKS_SERVICE_TRANSITION`. Census service-wide tìm thấy một
   `dispatch_unconfirmed` **lịch sử đã hết hạn** trên thiết bị khác, không phải
   task mới đang chạy. Action `act_0f0a49c6424d42d3bc7bc49ad46e4ffa` chưa rõ
   kết quả; restart service ảnh hưởng mọi node nên phải đợi nó được hòa giải
   qua chủ sở hữu/luồng hiện hữu. Lời báo trước đó về công việc mới đã được sửa
   bằng census có lineage; không đổi action để làm preflight xanh.

Không có task/writer/lệnh đang chạy trên đúng thiết bị Windows tại các snapshot
cuối; census local cuối có **0 runner/VM**, canonical Job không active. Các
UNKNOWN/awaiting-acceptance lịch sử vẫn giữ trạng thái của chúng.

## Giới hạn nghiệm thu

Native child token chưa truy vấn thành công; host token non-elevated đã kiểm
tra. CPython fixture loader exit 126, .NET/AutoCAD production build chưa được
chứng minh. Native không tương đương hypervisor isolation. Không cấp native
approval cho build AutoCAD. Chưa đo VM cold-start/peak RAM, live idle reclamation,
network-loss canary hoặc end-to-end 100/20 acceptance từ ChatGPT.

## Tài nguyên ngoài repo và bước tiếp theo

Đã tải artifact inert, hash-verified, mode 0600 vào
`/home/svhome/.local/lib/codex-control-plane/releases/` trên
`svhome@100.116.112.22`. Archive release là
`codex-control-plane-native-first-1012-e707cccda6fc.tar.gz`.
Production Ubuntu vẫn PID **946413**, release r9 và source fingerprint cũ.
**Không stop/start/restart service, đổi policy/pilot/Scheduled Task, deploy,
release hoặc publish.**

Tiếp theo: lấy bằng chứng/handling hợp lệ cho ba UNKNOWN và một action trên node
khác; refresh global/local census; dùng helper cuối đã review để activate
metadata Ubuntu; chuyển Windows theo exact owner handoff; activate Codex-web
qua API hiện hữu và chạy prepared canary; chỉ sau đó xét chuyển Autocad.
Rollback source/package cũ được giữ, không dùng database restore để rollback code.

Helper cuối hash `5dbbd90823c5fc10111955d0f041affb3ee97231225ffc8b0b544f6e1500177b`
được review cho **upload/preflight**, chưa được chạy `--execute`. Census trước
stop và census sau stop chưa phải admission fence nguyên tử; việc execute sau
này còn phải chốt cửa sổ bảo trì/fence để tránh gián đoạn công việc mới tới.
Sau khi candidate bắt đầu, helper không tự stop lần nữa để rollback.

Git cuối: **main @ 7999c4151cb501db86f2e4d0a2275d33fc248324**, dirty/uncommitted,
không conflict. Các fixture Job đã terminal; không dispatch canary live.
