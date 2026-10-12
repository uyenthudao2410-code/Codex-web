# NEW one-file patch acceptance packet for r11

## Trạng thái và giới hạn

Đây là packet chuẩn bị cục bộ. Chưa dispatch, chưa áp dụng patch lên workspace, chưa tạo RUN/WAVE và chưa nghiệm thu semantic. Repository giữ target ở baseline có lỗi được chủ động tạo trong fixture opt-in.

Fixture kiểm chứng hành vi: patch đã áp dụng nhưng proof failed/timed_out phải yêu cầu replanning; proof passed mới được sẵn sàng cho controller nghiệm thu. Fixture không thay đổi mã sản phẩm.

`npm test` chọn `tests/*.test.js`; hai file nested `.cjs` này không khớp glob. Checker chỉ chạy khi chỉ định exact argv bên dưới. Không dùng `.coding-tools` làm đầu vào cho checker.

## Immutable packet

```json
{
  "observed_at": "2026-10-11T14:10:44.946Z",
  "source_head": "2c554f59cb7b8ffc86ce5e0e28076c792777642f",
  "target_path": "tests/fixtures/initial-proof-canary-target.cjs",
  "checker_path": "tests/fixtures/initial-proof-canary-check.cjs",
  "preimage_sha256": "90363c394e12dd67f9003ef96b033e739c7837b34c238238966df623d9e55650",
  "postimage_sha256": "d1edd529d09c7d4f71dfbb9e9b9e53010cc43a616cf1247594ddf4d705b84a1e",
  "postimage_bytes": 414,
  "patch_sha256": "77f2c282c91f3627e721d0d68bf1fa821bad21575ec136204353894b18ce5e4a",
  "checker_sha256": "059c4e83fcbeb07b293312988975b7267d8ab8428872e5ff1211dbf059800230",
  "plan_sha256": "235ecd2dc1bf8b49b21648ffd24df378088916e65e2420cb383fa79a6439afe7",
  "baseline": {
    "exit_code": 1,
    "pass": 2,
    "fail": 2,
    "stdout_sha256": "0533fd99211043bc4307b0ec927b08e75a04eb7647ff2314b31a82f66c561b0f",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  },
  "corrected": {
    "exit_code": 0,
    "pass": 4,
    "fail": 0,
    "stdout_sha256": "4c61a9f19fca191e5a9286e1454f0f2f18b9501792d15993868337f96b193f37",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  },
  "repo_target_still_baseline": true,
  "ordinary_npm_test_excluded": true
}
```

## Exact initial-verification plan

```json
{
  "argv": [
    "node",
    "--test",
    "tests/fixtures/initial-proof-canary-check.cjs"
  ],
  "cwd": "",
  "timeout_ms": 60000,
  "max_output_bytes": 32768
}
```

Plan SHA dùng canonical JSON keys sorted, UTF-8, separators compact; expiry không nằm trong plan EXACT4 keys. Recovery Host cung cấp `initial_verification_expires_at_ms` riêng trên native local workflow request đúng action expiry được cấp, không tái sử dụng hạn cũ. Không tự thêm trường nội bộ này vào request MCP Web public.

## Exact WriteExact envelope

Envelope UTF-8 dưới đây không có newline cuối; `patch_sha256` ở trên áp dụng đúng bytes này.

```text
*** Begin Patch
*** Write Exact File: tests/fixtures/initial-proof-canary-target.cjs
@@ encoding=zlib-base64 preimage_sha256=90363c394e12dd67f9003ef96b033e739c7837b34c238238966df623d9e55650 postimage_sha256=d1edd529d09c7d4f71dfbb9e9b9e53010cc43a616cf1247594ddf4d705b84a1e
+eJxlkMFqAzEMRO/+CvXkBLqbD1hyKPTeQ3srPai23BU4tpHkkBD238t2Cyn0Kr2Z0ch3JVATDuYn5w4HeGk2cAEMgZphCQSJL9aFRnibVxbFuHzBmUS5FuBiVIxrwZyvcGINGVU5Melql5AzRWhSa5rAZgJsTeqZItRCQ+JM0NDCDKeuBqGKUDCwGQ0+acYzVxld6iWsGZvPM2uryutgd9vUT61lpvi4Aa+G1hUWOMJt2cPNAXCC3V8SHo5HMOm0ByHrUsCXagNuWz/9St59Q1WK/mPkEnKPpLs/Efu7WgjjdUhVhvvrfmzuQMtY/OQW50419kwjXVoV0/XMf81gmdw3ucySYQ==
*** End Patch
```

Thay đổi duy nhất: điều kiện `['passed', 'failed', 'timed_out']` thành `['passed']` trong target. File checker không nằm trong patch.

## Local proof đã thực hiện

- Temp workspace riêng chứa đúng hai file ở cùng relative paths; dùng cùng argv checker.
- Baseline: exit 1, 2 PASS / 2 FAIL (failed và timed_out bị phân loại sai).
- Corrected temp copy: exit 0, 4 PASS / 0 FAIL.
- Temp đã được xóa sau khi xác minh absolute path; target trong repo vẫn khớp preimage SHA.
- Đây là local semantic regression proof, chưa chứng minh execution qua Sandbox hoặc attested native acceptance.

## Thực hiện live khi r11 và authority hiện hành đã sẵn sàng

1. Xác minh runtime r11/package/epoch mới thực sự ready, correct binding và registered root `E:\Github\Tools-Codex-web`; đối chiếu cả target preimage và checker SHA trước khi cấp action. Dừng nếu file khác digest.
2. Qua API được hỗ trợ, tạo task/context/writer/permission action MỚI cho đúng một target path, envelope SHA và plan ở packet này. Dùng action/attempt/idempotency keys mới; expiry phải thuộc quyền mới được duyệt và không vượt exec policy. Không replay patch hoặc RUN/WAVE lịch sử.
3. Gửi một approved-patch action có `verification` là exact plan. Recovery Host phải admit cả patch policy và exec policy trước ghi. Native workflow giữ approved-patch actor; thực thi một structured argv qua Sandbox sau patch và tạo source-bound ProofLedger evidence.
4. Nếu action trả running, chỉ quan sát đúng operation/action/attempt đã tạo; không submit lại. Đối chiếu patch effect, postimage SHA, plan SHA, proof_ids, proof_fingerprint, command/job cùng RUN/WAVE và epoch thực. Failed/timed_out phải giữ patch effect + REPLAN và không có passed proof fingerprint.
5. Muốn đóng khoảng trống nghiệm thu, cần phiên controller ChatWeb đã xác thực qua native MCP `task_control` action `accept` với đúng RUN/WAVE/proof của action mới. Không giả identity ChatWeb bằng bridge hoặc header. Nếu chưa có phiên/controller authority, báo acceptance pending và giữ evidence.
6. Sau acceptance thực, kiểm tra exact task/writer/context/Job đã terminal theo API; giữ standing scope theo quyền hiện hành. Không sửa/accept/reject pending RUN `95e909f0040a448faa9f1f3257e2ee2c` / WAVE `c101beadfc6d4f2fbc13845052c84693`.

## Điều kiện nghiệm thu

Chỉ gọi live end-to-end đạt khi cùng action mới chứng minh one-file patch, Sandbox Job exit 0 + checker 4/4, ProofLedger source binding và genuine attested native ChatWeb acceptance. Local temp proof và canary standalone không thay thế điều kiện này.
