# Task List: Redesign Control Center (Light Theme, Elegant Balance & Real Data)

- [x] 1. Architectural & Layout Design for Light Theme & Dynamic Data <!-- id: 0 -->
  - [x] Review all CSS design tokens in `control-center.css` & `dashboard.css` for light mode purity and dark mode compatibility <!-- id: 1 -->
  - [x] Audit all DOM elements in `index.html` and dynamic render logic in `dashboard.js` & `control-center.js` <!-- id: 2 -->
- [x] 2. Implementation: HTML Structure & Markup Refinement <!-- id: 3 -->
  - [x] Update filter bar in `index.html` with dynamic date, workspace title binding, and clean pill layout <!-- id: 4 -->
  - [x] Fix formatting templates for Donut legend, Tool ranking list, and Fleet table <!-- id: 5 -->
  - [x] Ensure all test IDs and required telemetry strings (`Phân tích Context & Chi phí`, `recent trace`, `MEASURED`, `ESTIMATED`, `SCENARIO`, etc.) are 100% preserved <!-- id: 6 -->
- [x] 3. Implementation: CSS Light Theme & Balanced Layout Styles <!-- id: 7 -->
  - [x] Update `dashboard.css` to implement a crisp, modern light theme by default (`#f8fafc`, `#ffffff`, `#e2e8f0`) with rich dark mode tokens under `body[data-theme="dark"]` <!-- id: 8 -->
  - [x] Fix squashed tool rows in Chart 3 (proper flex/grid columns for rank, tool name, stats, bar, cost) <!-- id: 9 -->
  - [x] Fix squashed donut legend items in Chart 2 (dot, name, count, percentage badges) <!-- id: 10 -->
  - [x] Perfect the 6 KPI cards, 3 Main chart columns, and 4 Subcards for balanced proportions and spacing <!-- id: 11 -->
  - [x] Polish SVG charts, line gradients, grid lines, and interactive hover tooltips for light/dark backgrounds <!-- id: 12 -->
  - [x] Style the Model Fleet Table with clean borders, headers, and status badges <!-- id: 13 -->
- [x] 4. Implementation: Real Data Binding in `dashboard.js` & `control-center.js` <!-- id: 14 -->
  - [x] Bind real workspace name to Project dropdown and real date dynamically <!-- id: 15 -->
  - [x] Dynamically populate the Model Fleet Table (`#daFleetTableBody`) from real model/delegation evidence <!-- id: 16 -->
  - [x] Compute real-time TPM, Latency, Anomaly detection, and Quick summary from live `performance` & `orchestration` trace <!-- id: 17 -->
  - [x] Ensure Donut and Tool bars render real tool telemetry with proper text formatting <!-- id: 18 -->
- [x] 5. Verification & Testing <!-- id: 19 -->
  - [x] Run `npm test` to verify all 234+ test suites pass cleanly <!-- id: 20 -->
  - [x] Verify light theme toggle and layout responsiveness <!-- id: 21 -->
  - [x] Review git status and staging invariants <!-- id: 22 -->

## Review & Verification Results
- **Theme**: Hoàn thiện toàn bộ giao diện Sáng (Light Theme) tinh tế, sang trọng với các token chuẩn `#f8fafc` / `#ffffff`, viền nhẹ `#e2e8f0`, đổ bóng mềm mại, đồng thời bảo lưu đầy đủ Dark Theme.
- **Bố cục & Căn chỉnh**: Sửa triệt để các lỗi dính chữ và tràn text ở Biểu đồ Donut (tách biệt cột tên, token, % thị phần), Bảng xếp hạng công cụ (huy hiệu rank, tên, progress bar, chi phí), 6 thẻ KPI, và 4 thẻ phụ.
- **Dữ liệu Thực**: Tự động liên kết ngày giờ thực tế (`📅 Hôm nay - 19/08/2026`), tên workspace thực tế (`Codex-web`), hiển thị đầy đủ Bảng hiệu quả mô hình (Fleet Table), TPM/độ trễ và cảnh báo thực tế từ MCP telemetry trace và orchestration ledger.
- **Test Suite**: 234/234 test pass 100% không có hồi quy nào (`dashboard-analytics.test.js`, `control-panel.test.js`, v.v.).
