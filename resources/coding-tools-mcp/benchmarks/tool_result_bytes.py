from __future__ import annotations

"""Deterministic dogfood benchmark for serialized tool-result bytes.

Runs a fixed, side-effect-minimal workload against a synthetic workspace and
reports task completion, tool-call count, and serialized tool-result bytes
(the byte cost a model client pays for every tool result). Mirrors the spirit
of the upstream benchmark: smaller results are only meaningful when completion
stays identical, and elapsed time is reported but not treated as a proxy for
quality.

Usage:
    python -m benchmarks.tool_result_bytes [--runs N] [--output DIR]
"""

import argparse
import json
import os
import statistics
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from coding_tools_mcp.server import Runtime  # noqa: E402


def build_fixture(root: Path) -> None:
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "src" / "core.py").write_text(
        "def add(a, b):\n    return a + b\n\n\ndef main():\n    print(add(1, 2))\n",
        encoding="utf-8",
    )
    (root / "src" / "util.py").write_text(
        "def banner():\n    return 'fixture-util'\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        "# Fixture\n\nA small synthetic project used by the deterministic dogfood benchmark.\n",
        encoding="utf-8",
    )


def serialize_bytes(result: dict) -> int:
    return len(json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def run_workload(root: Path) -> dict:
    with patch.dict(os.environ, {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
        runtime = Runtime(root)
    calls: list[tuple[str, dict]] = [
        ("workspace_context", {}),
        ("read_file", {"path": "src/core.py"}),
        ("read_file", {"path": "src/util.py"}),
        ("read_file", {"path": "README.md"}),
        ("list_dir", {"path": "src"}),
        ("search_text", {"query": "def", "path": "src"}),
        ("exec_command", {"cmd": "echo deterministic-dogfood-ok", "yield_time_ms": 2000, "max_output_bytes": 4096, "verbosity": "full"}),
        ("apply_patch", {
            "patch": (
                "*** Begin Patch\n"
                "*** Update File: README.md\n"
                "@@\n"
                " # Fixture\n"
                "+Benchmark patched this file.\n"
                "*** End Patch\n"
            )
        }),
        ("git_status", {}),
    ]
    results: list[dict] = []
    errors: list[str] = []
    try:
        for name, args in calls:
            result = runtime.call_tool(name, dict(args))
            results.append(result)
            if result.get("isError") or not result.get("structuredContent", {}).get("ok", True):
                structured = result.get("structuredContent", {})
                error = structured.get("error") or {}
                errors.append(f"{name}: {error.get('code')} {error.get('message')}")
    finally:
        runtime.close()
    return {"results": results, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--output", default=str(Path(__file__).resolve().parents[1] / "benchmarks" / "reports"))
    args = parser.parse_args()

    per_run: list[list[int]] = []
    completions: list[bool] = []
    tool_calls: list[int] = []
    elapsed: list[float] = []
    for _ in range(max(1, args.runs)):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_fixture(root)
            started = time.monotonic()
            outcome = run_workload(root)
            elapsed.append(time.monotonic() - started)
            per_run.append([serialize_bytes(result) for result in outcome["results"]])
            completions.append(not outcome["errors"])
            tool_calls.append(len(outcome["results"]))
            if outcome["errors"]:
                print("run errors:", outcome["errors"], file=sys.stderr)

    flattened = [size for run in per_run for size in run]
    report = {
        "benchmark": "serialized tool-result bytes",
        "runs": len(per_run),
        "task_completion": f"{sum(completions)}/{len(completions)}",
        "tool_calls_per_run": tool_calls[0] if tool_calls else 0,
        "serialized_result_bytes": {
            "total": sum(flattened),
            "median": statistics.median(flattened) if flattened else 0,
            "mean": round(statistics.mean(flattened), 1) if flattened else 0,
            "min": min(flattened) if flattened else 0,
            "max": max(flattened) if flattened else 0,
            "per_run_totals": [sum(run) for run in per_run],
        },
        "elapsed_seconds": {
            "total": round(sum(elapsed), 3),
            "median": round(statistics.median(elapsed), 3) if elapsed else 0,
        },
        "note": "Elapsed time is reported for completeness only; smaller results are meaningful only while task completion stays identical.",
    }

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = output_dir / f"tool-result-bytes-{stamp}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"report: {path}")
    return 0 if all(completions) else 1


if __name__ == "__main__":
    raise SystemExit(main())
