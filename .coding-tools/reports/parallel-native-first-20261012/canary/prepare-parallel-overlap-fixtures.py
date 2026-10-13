"""Plan by default; explicit preparation only seeds new additive fixture paths."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("parallel_overlap_canary", HERE / "run-parallel-overlap-canary.py")
CANARY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CANARY)


def plan_root(label, path):
    root = Path(path).resolve()
    actual = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=root, text=True).strip()).resolve()
    CANARY.base.require(root == actual, "REPOSITORY_ROOT_MISMATCH")
    fixture = root / CANARY.FIXTURE
    CANARY.base.require(fixture.resolve().is_relative_to(root) and not fixture.exists(), "NEW_FIXTURE_DIRECTORY_REQUIRED_DO_NOT_OVERWRITE")
    for ancestor in (root, *[root.joinpath(*Path(CANARY.FIXTURE).parts[:i]) for i in range(1, len(Path(CANARY.FIXTURE).parts))]):
        if ancestor.exists():
            info = os.lstat(ancestor)
            CANARY.base.require(not ancestor.is_symlink() and not getattr(info, "st_file_attributes", 0) & 0x400,
                                "FIXTURE_REPARSE_ANCESTOR_DENIED")
    files = CANARY.fixture_files(label)
    return {"workspace_label": label, "repository_root": str(root), "fixture": CANARY.FIXTURE,
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
            "native_argv": ["node", CANARY.FIXTURE + "/hold.cjs"], "native_cwd": "",
            "native_source_sha256": CANARY.base.sha(files[CANARY.FIXTURE + "/hold.cjs"]),
            "files": [{"path": name, "sha256": CANARY.base.sha(value), "size_bytes": len(value)} for name, value in files.items()]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-root", required=True)
    parser.add_argument("--autocad-root", required=True)
    parser.add_argument("--manifest-path")
    parser.add_argument("--prepare-fixtures", action="store_true")
    args = parser.parse_args()
    targets = [plan_root("Codex-web", args.codex_root), plan_root("Autocad", args.autocad_root)]
    CANARY.base.require(len({target["repository_root"].casefold() for target in targets}) == 2, "REPOSITORY_ROOTS_NOT_DISTINCT")
    plan = {"operation": "parallel_overlap_local_fixture_preparation", "prepared": False, "targets": targets,
            "shared_mcp_creation_claimed": False, "implementation_or_build_files_changed": False,
            "source_sha256": {name: CANARY.base.sha((HERE / name).read_bytes()) for name in
                              ("run-native-first-canary.py", "run-parallel-overlap-canary.py")}}
    if args.prepare_fixtures:
        manifest = Path(args.manifest_path or "")
        CANARY.base.require(manifest.is_absolute() and manifest.parent.resolve() == HERE and not manifest.exists(),
                            "NEW_LOCAL_PREPARATION_RECEIPT_REQUIRED")
        for target in targets:
            root = Path(target["repository_root"])
            (root / CANARY.FIXTURE).mkdir(parents=True)
            for relative, value in CANARY.fixture_files(target["workspace_label"]).items():
                with (root / relative).open("xb") as output:
                    output.write(value)
        plan.update(prepared=True, observed_at_ms=int(time.time() * 1000))
        with manifest.open("x", encoding="utf-8", newline="\n") as output:
            json.dump(plan, output, indent=2)
            output.write("\n")
    print(json.dumps(plan, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"operation": "parallel_overlap_local_fixture_preparation", "ok": False,
                          "error_code": CANARY.base.error_code(error)}))
        sys.exit(1)
