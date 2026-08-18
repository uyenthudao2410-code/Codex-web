from __future__ import annotations

from .workspace_truth import install_workspace_truth_guard


def main(argv: list[str] | None = None) -> int:
    from . import server

    install_workspace_truth_guard(server)
    return server.main(argv)
