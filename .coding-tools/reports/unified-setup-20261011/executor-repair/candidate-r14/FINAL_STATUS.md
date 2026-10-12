# r14 — kết quả kiểm chứng thực tế

Quan sát cuối: **12/10/2026, 07:36:08 (giờ Việt Nam)**.

## Đã hoàn tất

- Kích hoạt `workflow-timeout-1012-r14` cho profile `web-mcp-assistant` trên DaoChienThang, đúng `E:\Github\Tools-Codex-web`.
- Runtime **READY**; kết nối trung tâm và quyền sẵn sàng. Mã Host/UI/native đang chạy khớp mã trên đĩa.
- Một lần sửa → chạy kiểm tra → proof đi qua Ubuntu MCP service và Windows bridge đã thành công. Bản vá thực sự được áp dụng; Job gốc thoát **0**, proof gắn đúng source đạt, không dùng cache. Receipt trung tâm là **completed**.
- Task trung tâm đã đóng, writer đã nhả. Kiểm tra cuối có **0 Job/lệnh/tác vụ nền đang chạy**, không drift hoặc tài nguyên không rõ chủ.
- Bốn policy được giữ nguyên. Quyền thử vẫn hết **10:42:51.067 ngày 12/10/2026**.

Lỗi timeout workflow 12 giây được sửa bằng một deadline chung bao phủ thời gian chuẩn bị Sandbox, chạy kiểm tra và nhận kết quả. Bản vá được gửi một lần; quan sát tiếp cùng workflow và Job.

## Bằng chứng

| Kiểm tra | Kết quả |
| --- | --- |
| Test nguồn tập trung cho initial verification | 3/3 đạt |
| Payload đóng gói so với nguồn | 17/17 khớp |
| Packaged Recovery smoke | Đạt |
| Lần chạy MCP thực tế | Patch áp dụng, Job exit 0, proof passed, receipt completed |
| Trạng thái cuối | READY, 0 hoạt động thực thi đang chạy |

Các test nguồn/package đã có bằng chứng trên đúng mã được đóng gói; không chạy lại chúng trong bước chốt báo cáo. Proof nguồn được chụp trước khi cập nhật tài liệu này.

## Hai phần chưa đủ bằng chứng

1. **Chưa thu được TAP đầy đủ của Job gốc.** Công cụ đọc output bị timeout; output chỉ giữ 300 giây và đã hết hạn. Durable summary không có TAP. Không tuyên bố 4/4 live TAP và không chạy lại checker để thay bằng chứng gốc.
2. **ChatWeb chưa hoàn tất acceptance.** Phiên Codex này không có transport công cụ native để controller thực hiện acceptance. Ba native RUN đang chờ: hai RUN lịch sử và RUN r14. Việc đóng task trung tâm không thay thế acceptance.

Sandbox vẫn cư trú (**3 host process / 1 backend**) để dùng tiếp; không có Job chạy. Không dùng bằng chứng zero-VM trước canary để mô tả trạng thái này.

## Bước tiếp theo tại MCP web

Dùng phiên ChatWeb có connector đã kết nối để quan sát kết quả gốc, review và hoàn tất acceptance nếu công cụ hiện tại hỗ trợ. Có thể gửi nội dung sau trong phiên đó:

```text
Tiếp tục nghiệm thu r14 của Tools-Codex-web trên DaoChienThang, thư mục E:\Github\Tools-Codex-web.
Quan sát action act_f362cf6605b54b02a74df1778bf9c973 của binding bind_3e05bf64cb3e4bab93d930ae1692bebb.
Job gốc: 94b54216ffb64174a64c68c77b7e08f9; proof: 820e07686998402abc95b92ce1063c4a.
RUN: 6664f948cfb14a75958518548352896e; WAVE: edf9fd5a6cf744dfa15a47d6e6206098.
Review kết quả gốc và hoàn tất acceptance bằng công cụ được công bố nếu phiên này có đúng quyền controller.
TAP đầy đủ chưa thu được; không báo 4/4. Không gửi lại bản vá hoặc chạy lại checker. Nếu không có action acceptance, báo chính xác công cụ còn thiếu.
```

## Phạm vi thay đổi và trạng thái Git

- Windows: r14 đã được kích hoạt; intake/pilot Ubuntu chuyển trong đúng phạm vi và hạn đã duyệt; task/writer thử nghiệm đã được dọn qua API hỗ trợ.
- Mã sửa liên quan: `electron/services/runtimeOrchestrator.js`, `tests/control-plane-approved-patch-runtime.test.js`. Báo cáo hiện tại: `docs/CURRENT_STATE.md` và evidence trong thư mục này.
- Git: dirty `main @ 2c554f59`; giữ các thay đổi ngoài phạm vi. Không commit, push hoặc phát hành.
- Không deploy/restart Ubuntu, gia hạn quyền hoặc reboot Windows trong rollout r14.

Receipt: [correlation](canary-same-window/correlation-1791764809860445100.json), [cleanup](canary-same-window/remote-receipts/cleanup-20261012T003108328507Z.json), [final census](canary-same-window/final-observation-1791765368847.json), [checkpoint](root-final-status-20261012.json).
