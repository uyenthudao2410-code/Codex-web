# Tasks: UI Enhancement for Cost Tab & Control Center

- [x] 1. Architecture & Design Specification <!-- id: 0 -->
  - [x] Analyze reference screenshot layout: Project Hero Header, 6 Financial KPI Cards, Search & Filter Toolbar, Master Cost Table (Left), Detail Inspector Drawer (Right) <!-- id: 1 -->
  - [x] Define comprehensive design system tokens (Light theme primary, Dark theme supported, Plus Jakarta Sans typography, sleek card shadows, refined pills & status badges) <!-- id: 2 -->
- [x] 2. Implementation: HTML Structure & Markup <!-- id: 3 -->
  - [x] Create `renderer/cost-tab.html` as a standalone interactive viewer with mock construction project data (DA2532 - Ký túc xá WISTRON) <!-- id: 4 -->
  - [x] Embed Cost Management view (`<section data-page-view="cost">`) and navigation tab (`CP - Chi phí DA`) into `renderer/index.html` <!-- id: 5 -->
- [x] 3. Implementation: CSS Stylesheet (`renderer/cost-tab.css`) <!-- id: 6 -->
  - [x] Implement Project Hero Card (Thumbnail, Project meta, Value 28 tỷ, Radial progress gauge, live status pills) <!-- id: 7 -->
  - [x] Implement 6 Financial KPI Metric Cards (Total Cost 3.42 tỷ, Approved, Pending Approval, Paid, Remaining, Overdue) <!-- id: 8 -->
  - [x] Implement Search & Filter Toolbar with dropdowns, date picker, search input, and action buttons <!-- id: 9 -->
  - [x] Implement Master-Detail layout: Data table with sorting, category chips, money badges, approval pills, and action dropdown <!-- id: 10 -->
  - [x] Implement Detail Inspector Drawer with sub-tabs (General Info, Source Payments, Attachments, Approval Flow, Audit Log) <!-- id: 11 -->
  - [x] Add Modal "Thêm chi phí mới" and Toast notification system <!-- id: 12 -->
- [x] 4. Implementation: Interactive JavaScript Logic (`renderer/cost-tab.js`) <!-- id: 13 -->
  - [x] Add rich realistic dataset based on construction & enterprise project expenses (Materials, Labor, Transport, Heavy Machinery, Subcontractors) <!-- id: 14 -->
  - [x] Implement real-time search, multi-filter filtering, column sorting, and pagination <!-- id: 15 -->
  - [x] Implement Master-Detail selection: click row to load detail into inspector drawer with smooth animation <!-- id: 16 -->
  - [x] Implement Add Expense modal with form validation, quick approval actions, and export simulation <!-- id: 17 -->
- [x] 5. Verification & Testing <!-- id: 18 -->
  - [x] Run `npm test` to ensure all 238 test suites continue to pass without regression <!-- id: 19 -->
  - [x] Test layout balance, responsive master-detail resizing, interactive filtering, and drawer toggle <!-- id: 20 -->
  - [x] Check coding-tools delivery and git invariants <!-- id: 21 -->

## Review & Verification Results
- **Hoàn thiện UI Tab Chi Phí**: Tạo thành công trang giao diện chuyên nghiệp tại [`renderer/cost-tab.html`](file:///e:/DEV/Codex-web/renderer/cost-tab.html), [`renderer/cost-tab.css`](file:///e:/DEV/Codex-web/renderer/cost-tab.css), [`renderer/cost-tab.js`](file:///e:/DEV/Codex-web/renderer/cost-tab.js).
- **Thiết kế chuẩn Enterprise**: Layout Master-Detail cân đối tinh tế, 6 thẻ KPI tài chính trực quan, thanh lọc đa tiêu chí, drawer inspector xem chi tiết chi phí với 4 tab con, modal tạo phát sinh chi phí mới và hỗ trợ chuyển đổi Light/Dark theme.
- **Kiểm thử**: 238/238 test pass 100%, bảo đảm toàn bộ hệ thống vận hành trơn tru.
