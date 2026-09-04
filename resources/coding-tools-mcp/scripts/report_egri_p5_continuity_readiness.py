#!/usr/bin/env python3
"""Report TG11 EGRI/P5 continuity readiness without opening a study."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.egri_p5_continuity_readiness import (  # noqa: E402
    egri_p5_continuity_readiness,
)
from coding_tools_mcp.semantic_localization import (  # noqa: E402
    semantic_localizer_from_env,
    semantic_provider_status,
)


MAX_INPUT_BYTES = 64 * 1024


def _read_object(path: Path | None, *, unwrap_result: bool = False) -> dict[str, object] | None:
    if path is None:
        return None
    resolved = path.resolve(strict=True)
    if resolved.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError(f"{resolved.name} exceeds the 64 KiB contract limit")
    value = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{resolved.name} must contain a JSON object")
    if unwrap_result and value.get("ok") is True and isinstance(value.get("result"), dict):
        return value["result"]
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--tg10-report", type=Path, required=True)
    parser.add_argument("--common-baseline-acceptance", type=Path)
    parser.add_argument("--egri-preregistration", type=Path)
    parser.add_argument("--aa-health-receipt", type=Path)
    parser.add_argument(
        "--semantic-status",
        type=Path,
        help="Optional content-free status receipt; otherwise inspect the configured read-only provider.",
    )
    args = parser.parse_args(argv)
    root = args.workspace.resolve(strict=False)
    try:
        rotation = _read_object(args.tg10_report, unwrap_result=True)
        if rotation is None:
            raise ValueError("TG10 report is required")
        baseline = _read_object(args.common_baseline_acceptance)
        preregistration = _read_object(args.egri_preregistration)
        aa_health = _read_object(args.aa_health_receipt)
        semantic = _read_object(args.semantic_status, unwrap_result=True)
        semantic_source = "explicit_content_free_receipt"
        if semantic is None:
            semantic = semantic_provider_status(semantic_localizer_from_env(root))
            semantic_source = "configured_read_only_provider_status"
        result = egri_p5_continuity_readiness(
            rotation,
            common_baseline_acceptance=baseline,
            preregistration=preregistration,
            aa_health_receipt=aa_health,
            semantic_status=semantic,
        )
        result["observation"] = {
            "semantic_status_source": semantic_source,
            "canonical_writer_instantiated": False,
            "ledger_opened": False,
            "study_store_opened": False,
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
