# W6 — Phát hành tích hợp CoS/WebCodex vào Codex-web: nghiệm thu

Ngày: 2026-10-23 (Asia/Ho_Chi_Minh). Phạm vi được user duyệt toàn bộ lúc 19:43 +07:
commit + push + đồng bộ 3 máy + build + live smoke.

## 1. Kết quả chính

| Hạng mục | Kết quả |
|---|---|
| Commit tính năng | `157476a6` — feat(integration): merge CoS/WebCodex program W1–W5 into Codex-web (native chat, goal continuation, job input receipts, git range review, browser session generations) — đúng **39 file**, +4705/−30 |
| Commit snapshot | `a3818ce3` — chore(coding-tools): delivery snapshot for CoS/WebCodex integration W1–W5 (12 file `.coding-tools`) |
| HEAD trước → sau | `cc35c120` (khi chốt bước 0) → `157476a6`; main sau đó trôi tiếp `1df4c334` (sửa test PID-file của phiên song song, không giao file chương trình) |
| Build | tag `r19-cos-integration`; exe SHA-256 `E616EE7CC3CA626B95CEA22F4D9C16FD0B90AE33E69D6BD91A431E5CCED7E03B`; installation `2054aede8be9a0cdea624b5b0eb044ff9270bfeeb75b5fae13be3b706e6d777d` |
| Kích hoạt | epoch `activation-mvl0xg6q-94fd3d123910de38ae84ead80f30f95d` — **READY, admission_open=true, fully_ready=true, central_connected=true, update_incomplete=false**; host/UI revision running == disk |
| Live smoke | **PASS trên bản đóng gói** (mục 4) |
| Rollback | Không cần dùng; vị trí rollback còn nguyên (mục 5) |

## 2. Bước 0 — hội tụ với main đang trôi

- Các commit sau điểm hội tụ `e52ed53b` tới HEAD khi chốt (`cc35c120`): thay đổi ngoài
  chương trình chỉ gồm `src/tool_runtime/jobs.rs` (fix validation_handoff của phiên khác),
  `package-lock.json` (js-yaml 4.2), và file docs backlog.
- Giao với 39 file delta của chương trình = **rỗng** → không phải merge lại.

## 3. Kiểm thử trên Windows (trước commit, checkout `E:\DEV\Codex-web`)

- Node: **133/133 PASS** — cos-companion-adapter 12, work-hub-diff-view 4, work-hub-files 20,
  work-hub-codex-chat 10, work-hub-git-review 4, work-hub-browser-qa-session 3, work-hub-ui 15,
  work-hub-store 25, work-hub-scope 6, work-hub-coordination 6, work-hub-jobs 11, settings 15,
  codex-desktop-config 2.
- Python (PYTHONPATH=`python_vendor;.`): **126/126 OK** — test_continuation_send_state 15,
  test_continuation_goal_wiring 4, test_job_input 10, test_codex_bridge 23,
  test_goal_pursuit 12, test_run_continuation 50, test_coordination_state 12.
- `check_module_size.py`: ok.
- Nghi thức delivery: `npm run stage:coding-tools-delivery` PASS;
  `npm run check:coding-tools-delivery` **PASS (11312 files)**. Commit bằng pathspec sau khi
  xem toàn bộ `git diff --cached`; nội dung trên GitHub đã đối chiếu byte (sha256 blob của
  `job_input.py`, `workHubCodexChat.js`, `codex_bridge.py` khớp cây hội tụ, LF được giữ).

## 4. Đồng bộ 3 máy

- **Windows**: checkout tại `157476a6` sau rebase + push.
- **svhome**: `~/DEV/Codex-web` tự pull (autopull) tới `157476a6` (WIP telemetry của phiên
  khác không bị đụng); cây copy `~/Codex-web` nhận đủ 39/39 file; smoke: `node --check`
  3 service mới OK, `tests/work-hub-git-review.test.js` 4/4 PASS.
- **VM**: snapshot `~/workspace/projects/Codex-web` nhận 39 file, `cmp` khớp toàn bộ.

## 5. Build + kích hoạt (theo runbook r18)

- Dừng stack bằng đường hỗ trợ (IPC `runtime.stop` trả `ORCHESTRATION_STATE_UNCERTAIN` —
  preflight timeout — nên dùng Uninstall supervisor + dừng tiến trình theo cây, diệt MCP
  python trước để nhả khóa ledger).
- Build lần 1 fail EBUSY khi ký exe (nghi Defender quét file mới); xóa output dở, build lại
  **exit=0**.
- Cài supervisor r19 (script trong build, `-Action Install -Packaged`), kích hoạt full-clean
  qua IPC Recovery Host `runtime.restart {refresh, full_clean_refresh, allowAcceptancePending}`
  → epoch mới READY (mục 1).
- **Rollback position**: các build cũ (r18, r17…) còn nguyên trong `dist\`; đường rollback đã
  drill hai chiều ngày 2026-10-23 (gỡ supervisor hiện tại → cài supervisor của build cũ →
  restart-refresh). Không phải dùng trong đợt này.

## 6. Live smoke trên bản đóng gói r19 (bằng chứng: `shot12-answer2.png`, `shot16-stopstate.png`, `smoke-receipt.json`)

- Provider: bridge tự tìm thấy Codex qua PATH (`%APPDATA%\npm\codex.cmd`, codex-cli **0.164.0**);
  biến `CODING_TOOLS_MCP_CODEX_BIN` trống và **không cần đặt**. Không xảy ra PROVIDER_UNAVAILABLE.
- Panel **Chat Codex (native)** — lượt 1: hỏi "Workspace nay dang o Git HEAD nao?" →
  trạng thái **"Lượt chat hoàn tất · Codex 0.164.0 · gpt-5.6-terra/medium · thread 01a16911"**,
  Codex trả lời đúng sự thật vừa tạo: *"Đang ở `main`, HEAD: `157476a6e9d5d121a5e985dcb684d2139273de9c`
  — `feat(integration): merge CoS/WebCodex program W1–W5 into Codex-web…`"* (đọc workspace thật qua
  bridge read-only; sự kiện turn/started → reasoning → commandExecution → turn/completed).
- Lượt 2 trên **cùng thread**: khảo sát cấu trúc thư mục — hoàn tất, trả lời bám đúng trạng thái
  repo (main/157476a6, `.coding-tools` chưa commit chỉ là ledger/task-context/performance).
- **Liên kết RUN** hiển thị id thật: RUN `e8cdbc78f12043559003ff65c4f6c883` · task
  `113674746a49401e9bc16264da7fcb5c` (lấy từ trạng thái tác vụ lúc tạo chat — không suy diễn).
- Lịch sử Codex Desktop của dự án hiển thị ở chế độ chỉ xem (bridge không tiếp tục thread Desktop).
- Nút **Dừng lượt**: đã bấm trong lượt 2 nhưng lượt hoàn tất trước khi lệnh dừng kịp hiệu lực —
  trạng thái cuối COMPLETED, chưa có bằng chứng INTERRUPTED trực tiếp (interrupt đã có ở mức test).
- Panel **ChatGPT companion (CoS)**: hiển thị đúng thiết kế — *"Companion đang tắt
  (cosCompanionEnabled=false). Khi tắt, Work Hub không thay đổi gì."*, nhãn Chỉ đọc · OBSERVED.
- Smoke job-input qua wire: **không thực hiện** — facade smart-v3 chưa mở `input_id`
  (additionalProperties=false, đã ghi ở W5); receipt đã kiểm ở lớp nội bộ bằng
  `test_job_input` 10/10 trên Windows.

## 7. Ma trận nghiệm thu T01–T10

Mức bằng chứng: source < test < integration < packaged < user-outcome.

| # | Hạng mục | Mức đạt | Ghi chú |
|---|---|---|---|
| T01 | Companion CoS quan sát read-only trong Work Hub (W1) | **packaged** (một phần) | Panel có trong r19 và tôn trọng mặc định tắt; theo đổi hướng 19:03 adapter chỉ là cầu tham chiếu tùy chọn — không còn app CoS trên máy để đọc phiên thật (đã gỡ sạch theo lệnh user) |
| T02 | File panel + unified diff + nhãn STALE (W2) | **test** | 157/157 ở W2; trên Windows work-hub-files 20/20 + diff-view 4/4; UI nằm trong bản r19 nhưng chưa chụp GUI riêng cho diff |
| T03 | Chat native một lượt qua Codex App Server (W3) | **packaged** | Live PASS: lượt 1 hoàn tất, trả lời đúng HEAD thật (mục 6) |
| T04 | Chat đa lượt + liên kết thread↔RUN + lịch sử Desktop chỉ xem (W3) | **packaged** | Live PASS: lượt 2 cùng thread 01a16911; link RUN/task id thật; lịch sử Desktop hiển thị |
| T05 | Dừng lượt (interrupt) + phân loại lỗi (W3) | **test** | Unit 10/10 gồm đường interrupt; thử trực tiếp không kịp (lượt xong trước), chưa có ảnh INTERRUPTED |
| T06 | Goal/Continuation: send-state 4 mức + handoff directive + episode gate (W4) | **test/integration** | Windows: send_state 15 + wiring 4 + hồi quy liên quan PASS; nối dây qua record_handoff_capsule hiện hữu trong MCP |
| T07 | Job input receipt delivered/unknown/rejected (W5) | **test** | test_job_input 10/10; wire facade chưa mở `input_id` — cần đợt schema + attestation riêng (đã ghi giới hạn ở W5) |
| T08 | Git range review (rename/numstat/fingerprint) (W5) | **test** | git-review 4/4 trên Windows và svhome; service chưa nối IPC/UI (để đợt sau) |
| T09 | Đóng gói + cài lại + kích hoạt full-clean (W6) | **packaged** | Build r19 exit=0, cài supervisor mới, epoch READY/fully_ready (mục 1, 5) |
| T10 | Rollback về bản trước | **integration** (drill) | Đã drill hai chiều với r18 ngày 2026-10-23; r19 kích hoạt thành công nên không rollback thật; build cũ còn nguyên làm vị trí lui |

Chưa mục nào đạt **user-outcome** — cổng này thuộc về user: mở app r19 và xác nhận trực tiếp
(mốc P0 trên bảng tiến trình giữ trạng thái chờ xác nhận).

## 8. Điểm chưa đạt / giới hạn đã biết

1. `input_id` chưa lên wire của facade smart-v3 → job-input receipt mới dùng được cho caller
   Python nội bộ (T07).
2. `workHubGitReview` chưa nối IPC/UI (T08).
3. Trạng thái FAILED ban đầu của panel chat khi mở app: một lần gọi bridge lúc khởi động
   (listHistory khi MCP chưa sẵn sàng) để lại state FAILED dính; probe sau đó thành công
   (hiện version 0.164.0) nhưng không tự xóa FAILED — gửi lượt mới vẫn chạy bình thường
   (đã chứng minh live). Nên sửa ở đợt sau: probe thành công nên đưa FAILED về READY khi
   chưa có thread/turn nào, hoặc listHistory lỗi không được ghi đè state.
4. Electron không lộ cây accessibility cho UIA (chỉ thấy khung cửa sổ) — tự động hóa GUI phải
   đi qua chuột/phím + screenshot; không ảnh hưởng người dùng.
5. IPC `runtime.stop` trả `ORCHESTRATION_STATE_UNCERTAIN` khi dừng để build (preflight
   timeout) — đã xử lý bằng đường hỗ trợ; nên xem lại ở đợt ổn định hoá.
