#!/usr/bin/env python3
"""Report the TG12 evidence-only disposition without changing product policy."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.trusted_resolution_decision_gate import (  # noqa: E402
    trusted_resolution_decision_gate,
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
    parser.add_argument("--tg11-readiness", type=Path, required=True)
    parser.add_argument("--outcome-receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        readiness = _read_object(args.tg11_readiness, unwrap_result=True)
        if readiness is None:
            raise ValueError("TG11 readiness report is required")
        outcome = _read_object(args.outcome_receipt, unwrap_result=True)
        result = trusted_resolution_decision_gate(
            readiness,
            outcome_receipt=outcome,
        )
        result["observation"] = {
            "canonical_writer_instantiated": False,
            "ledger_opened": False,
            "study_store_opened": False,
            "production_policy_surface_called": False,
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
