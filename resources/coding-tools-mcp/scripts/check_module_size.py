#!/usr/bin/env python3
"""Module-size guard for the Coding Tools MCP package.

Fails CI when a module crosses its line budget without an explicit
allowlist entry. The budgets exist so feature work lands in the module
that owns its domain instead of accumulating in server.py (see
AGENTS.md). Raise a budget deliberately, with a named reason, instead
of deleting this check.
"""

from __future__ import annotations

import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "coding_tools_mcp"

# Absolute line budgets. Values below current size plus headroom.
BUDGETS: dict[str, int] = {
    "server.py": 3500,
    "orchestration_ledger.py": 5000,
}
DEFAULT_BUDGET = 1600

ALLOWLIST: dict[str, tuple[int, str]] = {
    # (override budget, reason) — re-review whenever the reason drifts.
    # These bounded increases cover the already-landed Revision-4 control and
    # read-model bridges; they are explicit so future growth still fails closed.
    "coordination.py": (1700, "Revision-4 PRL and task-control authority bridge"),
    "mcp_http_handler.py": (1750, "MCP-2026 stateless context and typed transport envelope"),
    "orchestration_ledger.py": (5300, "bounded live-run projection and acceptance telemetry"),
    "solution_economics.py": (1700, "Revision-4 descriptive problem-resolution analytics"),
}


def main() -> int:
    failures: list[str] = []
    for path in sorted(PACKAGE_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        lines = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
        budget = ALLOWLIST.get(path.name, (BUDGETS.get(path.name, DEFAULT_BUDGET), ""))[0]
        if lines > budget:
            failures.append(f"{path.name}: {lines} lines > budget {budget}")
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        print(
            "Module-size budget exceeded. Move the new code into the module that "
            "owns its domain (see resources/coding-tools-mcp/AGENTS.md) instead of "
            "raising a budget implicitly.",
            file=sys.stderr,
        )
        return 1
    print("module-size budgets ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
