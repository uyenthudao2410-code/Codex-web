"""Plan by default; explicit --prepare-fixtures seeds a new additive directory.

This is local fixture preparation, never evidence of shared MCP file creation.
No existing file or directory is replaced or deleted.
"""

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default="E:/DEV/Codex-web")
    parser.add_argument("--prepare-fixtures", action="store_true")
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    harness = runpy.run_path(str(here / "run-native-first-canary.py"))
    root = Path(args.repository).resolve()
    actual = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=root, text=True).strip()).resolve()
    if root != actual:
        raise RuntimeError("REPOSITORY_ROOT_MISMATCH")
    fixture = root / harness["FIXTURE"]
    if not fixture.resolve().is_relative_to(root) or fixture.exists():
        raise RuntimeError("NEW_FIXTURE_DIRECTORY_REQUIRED_DO_NOT_OVERWRITE")
    files = [(harness["fixture_path"](i), harness["fixture_content"](i).encode()) for i in range(1, 101)]
    files.append((harness["FIXTURE"] + "/trusted-build.js", harness["build_source"]().encode()))
    plan = {"operation": "native_first_local_fixture_preparation", "prepared": False,
            "repository": str(root), "fixture": harness["FIXTURE"], "seed_file_count": 100,
            "trusted_build_argv": ["node", "trusted-build.js"], "trusted_build_cwd": harness["FIXTURE"],
            "shared_mcp_creation_claimed": False, "files": [
                {"path": path, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)} for path, data in files]}
    if args.prepare_fixtures:
        manifest_path = here / "fixture-preparation.json"
        if manifest_path.exists():
            raise RuntimeError("PREPARATION_RECEIPT_EXISTS_DO_NOT_OVERWRITE")
        fixture.mkdir()
        for path, data in files:
            with (root / path).open("xb") as output:
                output.write(data)
        plan.update({"prepared": True, "observed_at_ms": int(time.time() * 1000),
                     "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
                     "harness_sha256": hashlib.sha256((here / "run-native-first-canary.py").read_bytes()).hexdigest()})
        with manifest_path.open("x", encoding="utf-8", newline="\n") as output:
            json.dump(plan, output, indent=2)
            output.write("\n")
    print(json.dumps(plan, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print(json.dumps({"operation": "native_first_local_fixture_preparation", "ok": False, "error_code": code}))
        sys.exit(1)
