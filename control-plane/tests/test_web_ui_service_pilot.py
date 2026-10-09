from __future__ import annotations

import unittest

from control_plane.web_ui import WEB_UI_HTML, WEB_UI_JAVASCRIPT


class PrivateTunnelServiceConsoleTests(unittest.TestCase):
    def test_console_explains_shared_identity_and_exact_target_pilot(self) -> None:
        html = WEB_UI_HTML.decode("utf-8")
        javascript = WEB_UI_JAVASCRIPT.decode("utf-8")

        self.assertIn("Mỗi lời gọi qua tunnel dùng cùng một service principal", html)
        self.assertIn("không xác định người ChatGPT nào đã gọi", html)
        self.assertIn("Plus/Pro cá nhân lẫn Business", html)
        self.assertIn("workspace đã chọn trong app Windows", html)
        for element_id in (
            "mcp-service-principals-body",
            "mcp-service-grants-body",
            "scoped-pilot-decisions-body",
            "service-pilot-next-action",
        ):
            self.assertIn(f'id="{element_id}"', html)
            self.assertIn(f"'{element_id}'", javascript)
        self.assertIn("private_tunnel_service", javascript)
        self.assertIn("central scoped_pilot — local effect chưa được chứng minh", javascript)

    def test_personal_chatgpt_guidance_separates_connection_from_admin_scope(self) -> None:
        html = WEB_UI_HTML.decode("utf-8")
        javascript = WEB_UI_JAVASCRIPT.decode("utf-8")

        self.assertIn('<h2 id="service-pilot-title">ChatGPT qua private tunnel</h2>', html)
        self.assertIn("target: 'ChatGPT qua private tunnel'", javascript)
        self.assertNotIn("ChatGPT Business qua private tunnel", html + javascript)
        self.assertIn('<details id="personal-tunnel-help">', html)
        self.assertIn("Dùng với ChatGPT Plus / Pro cá nhân", html)
        self.assertIn("dùng lại kết nối đó", html)
        self.assertIn("Không cần tạo tunnel khác hay nhập Organization ID / ChatGPT Workspace ID vào Control Plane", html)
        self.assertIn("Thiết lập tunnel trên OpenAI Platform là bước quản trị riêng", html)
        self.assertIn("không phải ChatGPT Workspace ID", html)
        self.assertIn("Inventory chỉ kiểm tra metadata", html)
        self.assertIn("Grant chỉ xác thực tunnel, không tự cấp quyền sửa file/chạy lệnh", html)

    def test_browser_only_revokes_service_grant_and_pilot_with_csrf(self) -> None:
        html = WEB_UI_HTML.decode("utf-8")
        javascript = WEB_UI_JAVASCRIPT.decode("utf-8")

        self.assertIn("/v1/ui/mcp-service-grants/${encodeURIComponent(grantId)}/revoke", javascript)
        self.assertIn("/v1/ui/scoped-pilot-decisions/${encodeURIComponent(decisionId)}/revoke", javascript)
        self.assertIn("'X-Control-Plane-CSRF': csrfToken", javascript)
        self.assertNotIn("access_token", javascript)
        self.assertNotIn("localStorage", javascript)
        self.assertNotIn("id=\"open-admission\"", html)
        self.assertNotIn("/v1/ui/mcp-service-grants',", javascript)
        self.assertNotIn("/v1/ui/scoped-pilot-decisions',", javascript)


if __name__ == "__main__":
    unittest.main()
