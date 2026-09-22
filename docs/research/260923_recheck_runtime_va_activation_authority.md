# Recheck runtime và activation authority — 23/09/2026

Tài liệu này là snapshot read-only tiếp nối kế hoạch
`260922_ke_hoach_xu_ly_hai_problem_va_danh_gia_toan_dien_app.md`. Nó không
thay thế chronology cũ và không cấp thêm authority.

## 1. Git và phạm vi wave

```text
workspace = E:\DEV\Codex-web
branch = main
HEAD = c932d495fc0d6dff189930b13712167600208daf
origin/main = c932d495fc0d6dff189930b13712167600208daf
divergence = 0/0
working-tree-delta = .coding-tools/orchestration/ledger.sqlite3 only
```

Không dùng worktree. Không reset/rebase/force-push. Ledger live không bị sửa
thủ công và không được dùng làm lý do để mở lại candidate recovery cũ.

## 2. Runtime readback hiện tại

Supervisor và Recovery Host đang sống, nhưng đây mới là host liveness:

```text
Supervisor task_state = Running
Supervisor state = healthy
Recovery Host PID = 40120
runtime_mode = packaged
consecutive_failures = 0
last_spawned_pid = 40120
```

Authenticated boot observation lúc `2026-09-22T17:02:40Z` (= 00:02 ngày
23/09 +07) trả:

```text
workspace_matched = true
authority_granted = false
live_accepted = false

mcpRunning = false
nativeAlive = false
tunnelRunning = false
componentsReady = false
fullyReady = false
centralConnected = true
authorityReady = true
updateIncomplete = true
connectorRediscovered = false
connectorContractState = UNAVAILABLE
activation_state = UPDATE_INCOMPLETE
admission_open = false
```

`npm run dev:status` vẫn trả `DEV_UI_INSTALLATION_MISMATCH`. Development
`full-clean-activation --preflight` và `--status` đều trả
`RECOVERY_HOST_INSTALLATION_MISMATCH`. Đây là installation guard, không phải
lý do để sửa descriptor hoặc bypass identity.

## 3. Packaged artifact và source repair

Đã giải nén `app.asar` ra thư mục tạm ngoài repository bằng read-only
inspection:

```text
dist/win-unpacked/resources/app.asar SHA-256
  = 7944724624334C96AB02D7DB16213CD53E9D02BD3ED253FAD16904240F56CCE3

installed resources/app.asar SHA-256
  = 7944724624334C96AB02D7DB16213CD53E9D02BD3ED253FAD16904240F56CCE3

packaged electron/services/activationEpoch.js SHA-256
  = 77EB770D90EA8FDDD105639255CEBDA34B0FDA16B5A92D7D75FA2C28AD373C17

source electron/services/activationEpoch.js SHA-256
  = 77EB770D90EA8FDDD105639255CEBDA34B0FDA16B5A92D7D75FA2C28AD373C17
```

Như vậy artifact packaged đã chứa source repair. Tuy nhiên byte identity của
file không phải là bằng chứng full-clean activation đã thực thi thành công;
runtime hiện tại vẫn `UPDATE_INCOMPLETE`, primary MCP/Tunnel đều tắt và
admission đóng.

## 4. Canonical ledger và authority gate

Backup API census read-only lúc `2026-09-22T17:02:48.976Z`:

```text
logical_sha256 = 988e557c1ad10954f32e71927684e36cb527ab297942cee57fcdc771cd38964d
physical_sha256 = b65bf7e066b2929987f43fa2feefae14090dfbdb63c06741c2f8d372792e5b1e
schema_version = 12
integrity_check = ok
foreign_key_check_rows = 0
ordinary_active_runs = 17
p5_epochs = 6
unexplained_active_runs = 0
stale_background_operation_residues = 0
unbound_live_resource_residues = 0
mutated_canonical_ledger = false
```

Truy vấn trực tiếp `checkpoints.git_head` ở chế độ read-only cho thấy:

```text
current HEAD checkpoint rows = 0
current HEAD accepted checkpoint rows = 0
```

`accepted-code-activation.json` cũng không có authority đang hoạt động:

```text
active_checkpoint_id = null
closure_input = {}
intents = 0
processed_checkpoint_ids = 0
FULL_CLEAN_SOURCE_CHECKPOINT_JSON = absent
```

Accepted checkpoint gần nhất bind các HEAD cũ (`cffd2ace…` hoặc cũ hơn). Không
được gắn lại các checkpoint đó cho source hiện tại, vì full-clean contract yêu
cầu chính xác `checkpoint_id`, `run_id`, `wave_id`, `proof_fingerprint` và
`git_head`.

## 5. Quyết định và bước kế tiếp

Wave này không gọi `npm run dev:refresh`, `recovery:supervisor:once`, reboot,
raw IPC, descriptor edit, quarantine hay ledger import. Không tạo checkpoint
giả và không mở admission từ `REPORT_ACKNOWLEDGED`, test pass hoặc packaged
artifact.

Để hoàn thiện hai Problem, cần một acceptance wave chính thức tạo accepted
closure exact cho source/package hiện tại **hoặc** owner-authorized packaged
handoff có receipt identity tương ứng. Sau đó mới chạy full-clean activation,
xác minh MCP/native/Tunnel, strict `tools/list`/`server/discover`, một
`workspace_context` thật, reboot/logon oracle và natural-use/independent
outcome.

Trạng thái hiện tại là `SOURCE_PRESENT + FOCUSED_PROOF + PACKAGED_ARTIFACT +
RECOVERY_HOST_LIVE`, chưa phải `LIVE_ACCEPTED`; hai Problem tiếp tục `OPEN`.
