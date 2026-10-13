"""Verify and bind existing two-root overlap fixtures to the current r4 harness.

This is intentionally read-only with respect to both repositories.  It creates
only a new evidence manifest in this report directory, and refuses to overwrite
an existing manifest.  The generated manifest is suitable input to the
reviewed overlap approval and canary wrappers.
"""

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT_REPORT = HERE.parent
FIXTURE = "tests/fixtures/parallel-native-overlap-20261012"
LABELS = ("Codex-web", "Autocad")


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha(path):
    return sha_bytes(Path(path).read_bytes())


def load_runner():
    path = HERE / "run-parallel-overlap-canary.py"
    spec = importlib.util.spec_from_file_location("reviewed_overlap_runner", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_target(runner, label, root):
    repository = Path(root).resolve()
    actual = Path(subprocess.check_output(["git", "-C", str(repository),
                                           "rev-parse", "--show-toplevel"], text=True).strip()).resolve()
    require(actual == repository, "REPOSITORY_ROOT_MISMATCH")
    fixture = (repository / FIXTURE).resolve()
    require(fixture.is_dir() and not fixture.is_symlink() and fixture.is_relative_to(repository),
            "EXACT_EXISTING_FIXTURE_DIRECTORY_REQUIRED")
    records = []
    expected = runner.fixture_files(label)
    for relative, expected_bytes in expected.items():
        path = (repository / relative).resolve()
        require(path.is_file() and not path.is_symlink() and path.is_relative_to(fixture),
                "EXACT_EXISTING_FIXTURE_FILE_REQUIRED")
        actual_bytes = path.read_bytes()
        require(actual_bytes == expected_bytes, "OVERLAP_FIXTURE_CONTENT_CHANGED")
        records.append({"path": relative, "sha256": sha_bytes(actual_bytes),
                        "size_bytes": len(actual_bytes)})
    return {
        "workspace_label": label,
        "repository_root": str(repository),
        "fixture": FIXTURE,
        "git_head": subprocess.check_output(["git", "-C", str(repository),
                                               "rev-parse", "HEAD"], text=True).strip(),
        "native_argv": ["node", FIXTURE + "/hold.cjs"],
        "native_cwd": "",
        "native_source_sha256": sha_bytes(expected[FIXTURE + "/hold.cjs"]),
        "files": records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-root", required=True)
    parser.add_argument("--autocad-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    require(output.parent == HERE and not output.exists(), "NEW_OVERLAP_REUSE_MANIFEST_REQUIRED")
    runner = load_runner()
    targets = [verify_target(runner, "Codex-web", args.codex_root),
               verify_target(runner, "Autocad", args.autocad_root)]
    require(len({item["repository_root"].casefold() for item in targets}) == 2,
            "REPOSITORY_ROOTS_NOT_DISTINCT")
    manifest = {
        "operation": "parallel_overlap_fixture_reuse_preparation",
        "prepared": True,
        "targets": targets,
        "shared_mcp_creation_claimed": False,
        "implementation_or_build_files_changed": False,
        "source_sha256": {
            name: sha(HERE / name)
            for name in ("run-native-first-canary-timefix2.py", "run-parallel-overlap-canary-timefix2.py")
        },
        "observed_at_ms": int(time.time() * 1000),
        "mutations": 0,
        "source_scope": "additive read-only binding of existing fixture files to current r4 harness",
    }
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"operation": manifest["operation"], "ok": True,
                      "manifest_path": str(output), "source_sha256": manifest["source_sha256"]},
                     separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"operation": "parallel_overlap_fixture_reuse_preparation", "ok": False,
                          "error_code": str(error) if isinstance(error, RuntimeError) else type(error).__name__}))
        sys.exit(1)
