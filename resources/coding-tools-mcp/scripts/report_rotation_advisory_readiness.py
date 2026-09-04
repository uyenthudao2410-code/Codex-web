#!/usr/bin/env python3
"""Report TG10 rotation-advisory readiness without opening or assigning a study."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.cross_session_continuity_report import (  # noqa: E402
    CrossSessionContinuityFacts,
)
from coding_tools_mcp.ledger_analysis import open_ledger_analysis_snapshot  # noqa: E402
from coding_tools_mcp.natural_problem_cohort import (  # noqa: E402
    natural_problem_cohort_report,
)
from coding_tools_mcp.problem_resolution_economics import (  # noqa: E402
    ProblemLineageFacts,
)
from coding_tools_mcp.rotation_advisory_study import (  # noqa: E402
    rotation_advisory_study_readiness,
)


def _read_preregistration(path: Path | None) -> dict[str, object] | None:
    if path is None:
        return None
    resolved = path.resolve(strict=True)
    if resolved.stat().st_size > 65_536:
        raise ValueError("preregistration exceeds the 64 KiB contract limit")
    value = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("preregistration must be a JSON object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--start-problem-id", required=True)
    parser.add_argument("--start-problem-revision", required=True, type=int)
    parser.add_argument("--target-n", choices=(5, 10), default=10, type=int)
    parser.add_argument("--preregistration", type=Path)
    args = parser.parse_args(argv)
    root = args.workspace.resolve(strict=False)
    try:
        preregistration = _read_preregistration(args.preregistration)
        with open_ledger_analysis_snapshot(root) as snapshot:
            problems = ProblemLineageFacts.load(snapshot.reader)
            continuity = CrossSessionContinuityFacts.load(snapshot.reader)
            cohort = natural_problem_cohort_report(
                snapshot.ledger,
                problems,
                continuity,
                start_problem_id=args.start_problem_id,
                start_problem_revision=args.start_problem_revision,
                target_n=args.target_n,
            )
            result = rotation_advisory_study_readiness(
                cohort, preregistration=preregistration
            )
            result["snapshot"] = {
                "immutable_backup_api_copy": True,
                "total_fact_load_statements": snapshot.statement_count,
                "canonical_writer_instantiated": False,
                "live_backup_connections": snapshot.live_backup_connections,
            }
    except (json.JSONDecodeError, OSError, RuntimeError, TypeError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": type(exc).__name__,
                    "message": str(exc)[:500],
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
