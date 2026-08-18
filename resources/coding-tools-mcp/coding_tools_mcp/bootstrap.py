from __future__ import annotations

from .workspace_truth import install_workspace_truth_guard


def main(argv: list[str] | None = None) -> int:
    from . import server
    from .http_exception_boundary import ExceptionSafeMCPHandler

    install_workspace_truth_guard(server)
    server.MCPHandler = ExceptionSafeMCPHandler
    return server.main(argv)
