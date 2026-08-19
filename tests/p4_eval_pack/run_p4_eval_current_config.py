from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def find_repo_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        reporter = candidate / "resources" / "coding-tools-mcp" / "scripts" / "report_p4_readiness.py"
        if reporter.is_file():
            return candidate
    return None


def _extract_json_objects(text: str):
    decoder = json.JSONDecoder()
    for idx, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[idx:])
        except Exception:
            continue
        if isinstance(obj, dict):
            yield obj


def _normalize_signals(value):
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return sorted(str(v) for v in value)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                parsed = json.loads(stripped)
            except Exception:
                try:
                    parsed = ast.literal_eval(stripped)
                except Exception:
                    parsed = None
            if isinstance(parsed, list):
                return sorted(str(v) for v in parsed)
        if not stripped:
            return []
        return [stripped]
    return [str(value)]


def extract_readiness_snapshot(text: str) -> dict:
    wanted = ("ready", "status", "failure_class", "validated_signals")

    # Prefer structured JSON anywhere in the reporter output.
    candidates = list(_extract_json_objects(text))
    for obj in reversed(candidates):
        stack = [obj]
        while stack:
            current = stack.pop()
            if not isinstance(current, dict):
                continue
            if any(k in current for k in wanted):
                snap = {}
                if "ready" in current:
                    snap["ready"] = bool(current["ready"])
                if "status" in current:
                    snap["status"] = str(current["status"])
                if "failure_class" in current:
                    snap["failure_class"] = None if current["failure_class"] is None else str(current["failure_class"])
                if "validated_signals" in current:
                    snap["validated_signals"] = _normalize_signals(current["validated_signals"])
                if snap:
                    return snap
            stack.extend(v for v in current.values() if isinstance(v, dict))

    # Fallback for key/value text reporters.
    snap = {}
    patterns = {
        "ready": r"(?im)^\s*ready\s*[:=]\s*(true|false)\b",
        "status": r"(?im)^\s*status\s*[:=]\s*['\"]?([A-Za-z0-9_.-]+)",
        "failure_class": r"(?im)^\s*failure_class\s*[:=]\s*['\"]?([A-Za-z0-9_.-]+|none|null)",
        "validated_signals": r"(?im)^\s*validated_signals\s*[:=]\s*(\[[^\r\n]*\]|[^\r\n]+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if not match:
            continue
        raw = match.group(1).strip()
        if key == "ready":
            snap[key] = raw.lower() == "true"
        elif key == "failure_class":
            snap[key] = None if raw.lower() in {"none", "null"} else raw.strip("'\"")
        elif key == "validated_signals":
            snap[key] = _normalize_signals(raw)
        else:
            snap[key] = raw.strip("'\"")
    return snap


def run_reporter(repo_root: Path) -> dict:
    reporter = repo_root / "resources" / "coding-tools-mcp" / "scripts" / "report_p4_readiness.py"
    proc = subprocess.run(
        [sys.executable, str(reporter), "--workspace", str(repo_root)],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    combined = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return {
        "command": [sys.executable, str(reporter), "--workspace", str(repo_root)],
        "exit_code": proc.returncode,
        "snapshot": extract_readiness_snapshot(combined),
        "output_tail": combined[-4000:],
    }


def run_isolated_battery() -> dict:
    # Reuse the already-tested isolated battery implementation.
    sys.path.insert(0, str(HERE))
    from run_p4_eval_battery import Battery  # type: ignore

    return Battery().run()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="P4 capability-aware evaluation runner for the current repository configuration."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root. Auto-detected from the runner location when omitted.",
    )
    parser.add_argument(
        "--require-reporter",
        action="store_true",
        help="Fail if the canonical P4 readiness reporter is not available or cannot be parsed.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve() if args.repo_root else find_repo_root(HERE)
    reporter_available = bool(repo_root)

    result = {
        "runner": "p4-current-config-v1",
        "execution_model": "host_python_capability_aware",
        "runtime_capabilities": {
            "live_task_control_ack": "not_required_for_this_battery",
            "canonical_reporter": reporter_available,
            "synthetic_canonical_promotion": False,
        },
        "repo_root": str(repo_root) if repo_root else None,
        "canonical_readiness_before": None,
        "isolated_battery": None,
        "canonical_readiness_after": None,
        "canonical_readiness_non_interference": None,
        "status": "FAIL",
    }

    try:
        before = run_reporter(repo_root) if repo_root else None
        if before is not None:
            result["canonical_readiness_before"] = before
            if before["exit_code"] != 0:
                raise RuntimeError(f"canonical readiness reporter BEFORE failed with exit code {before['exit_code']}")
            if args.require_reporter and not before["snapshot"]:
                raise RuntimeError("canonical readiness reporter BEFORE output could not be parsed")

        battery = run_isolated_battery()
        result["isolated_battery"] = {
            "checks": battery["checks"],
            "canonical_promotion_mutated": battery["canonical_promotion_mutated"],
            "metrics": battery["metrics"],
            "limitations": battery["limitations"],
        }
        if battery["checks"]["failed"] != 0:
            raise RuntimeError("isolated battery reported failures")
        if battery["canonical_promotion_mutated"] is not False:
            raise RuntimeError("isolated battery unexpectedly mutated canonical promotion evidence")

        after = run_reporter(repo_root) if repo_root else None
        if after is not None:
            result["canonical_readiness_after"] = after
            if after["exit_code"] != 0:
                raise RuntimeError(f"canonical readiness reporter AFTER failed with exit code {after['exit_code']}")
            if args.require_reporter and not after["snapshot"]:
                raise RuntimeError("canonical readiness reporter AFTER output could not be parsed")

            if before and before["snapshot"] and after["snapshot"]:
                unchanged = before["snapshot"] == after["snapshot"]
                result["canonical_readiness_non_interference"] = {
                    "status": "PASS" if unchanged else "FAIL",
                    "before": before["snapshot"],
                    "after": after["snapshot"],
                }
                if not unchanged:
                    raise RuntimeError("canonical readiness changed after isolated synthetic battery")
            else:
                result["canonical_readiness_non_interference"] = {
                    "status": "NOT_APPLICABLE",
                    "reason": "canonical reporter output was not semantically parseable; isolated battery still completed",
                }
                if args.require_reporter:
                    raise RuntimeError("canonical readiness non-interference could not be proven")
        else:
            result["canonical_readiness_non_interference"] = {
                "status": "NOT_APPLICABLE",
                "reason": "canonical reporter not present in this execution environment",
            }
            if args.require_reporter:
                raise RuntimeError("canonical readiness reporter not available")

        result["status"] = "PASS"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    out = HERE / "p4_eval_current_config_report.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "report": str(out),
        "runtime_capabilities": result["runtime_capabilities"],
        "canonical_readiness_non_interference": result["canonical_readiness_non_interference"],
        "isolated_checks": (result["isolated_battery"] or {}).get("checks"),
        "error": result.get("error"),
    }, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
