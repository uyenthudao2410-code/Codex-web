from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(r"E:\DEV\Tools-Codex-web")
sys.path.insert(0, str(ROOT / "resources" / "coding-tools-mcp"))

from coding_tools_mcp.server import Runtime

patch = Path(sys.argv[1]).read_text(encoding="utf-8-sig").lstrip("\ufeff").strip()
runtime = Runtime(ROOT, permission_mode="dangerous")
try:
    result = runtime.apply_patch({"patch": patch, "dry_run": False})
    print(json.dumps(result, ensure_ascii=False, indent=2))
finally:
    runtime.close()

