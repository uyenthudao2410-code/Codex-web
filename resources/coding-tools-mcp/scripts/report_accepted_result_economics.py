from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.accepted_result_economics_report import accepted_result_economics_report
from coding_tools_mcp.ledger_access import open_existing_ledger_analysis


def _git(workspace: Path, *args: str) -> str:
    try:
        completed = subprocess.run(["git", *args], cwd=workspace, capture_output=True, text=True, check=False, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return ""
    return completed.stdout if completed.returncode == 0 else ""


def _source_worktree_clean(workspace: Path) -> bool | None:
    output = _git(workspace, "status", "--porcelain", "--untracked-files=all")
    if output == "" and not (workspace / ".git").exists():
        return None
    for raw in output.splitlines():
        path = raw[3:].strip().replace("\\", "/") if len(raw) >= 4 else raw.strip().replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        path = path.strip('"')
        if path and not path.startswith(".coding-tools/"):
            return False
    return True


def report(workspace: Path, *, limit: int = 5000, tail_n: int = 10) -> dict[str, object]:
    root = workspace.resolve()
    with open_existing_ledger_analysis(root) as snapshot:
        return accepted_result_economics_report(root, snapshot.ledger, source_head=_git(root, "rev-parse", "HEAD").strip().lower(), source_worktree_clean=_source_worktree_clean(root), limit=limit, tail_n=tail_n)


def main() -> int:
    parser = argparse.ArgumentParser(description="Report accepted-result time/resource economics without activating routing or experiments.")
    parser.add_argument("--workspace", default=str(REPOSITORY_ROOT))
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--tail-n", type=int, default=10)
    args = parser.parse_args()
    print(json.dumps(report(Path(args.workspace), limit=args.limit, tail_n=args.tail_n), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
