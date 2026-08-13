from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(r"E:\DEV\Tools-Codex-web")
sys.path.insert(0, str(ROOT / "resources" / "coding-tools-mcp"))

from coding_tools_mcp.server import Runtime

args_path = Path(sys.argv[1])
args = json.loads(args_path.read_text(encoding="utf-8-sig"))
patch_file = args.pop("__patch_file", None)
patch_files = args.pop("__patch_files", None)
if patch_file:
    args["patch"] = Path(patch_file).read_text(encoding="utf-8-sig").lstrip("\ufeff").strip()
if patch_files:
    args["patches"] = [Path(item).read_text(encoding="utf-8-sig").lstrip("\ufeff").strip() for item in patch_files]
if "patch" in args:
    print(json.dumps({"patch_prefix": repr(args["patch"][:32]), "patch_suffix": repr(args["patch"][-32:])}), file=sys.stderr)
runtime = Runtime(ROOT, permission_mode="dangerous")
try:
    result = runtime.agent_workflow(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
finally:
    runtime.close()

