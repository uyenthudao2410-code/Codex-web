"""Verify the existing native-first fixture for r4 without writing it."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(r"E:\DEV\Codex-web")
MAX_BYTES = 2 * 1024 * 1024


def require(value, code):
    if not value:
        raise RuntimeError(code)


def digest(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def read(file):
    path = Path(file)
    require(path.is_absolute() and path.is_file() and not path.is_symlink() and path.stat().st_size <= MAX_BYTES,
            "BOUNDED_ABSOLUTE_FIXTURE_EVIDENCE_REQUIRED")
    return json.loads(path.read_text(encoding="utf-8-sig")), digest(path)


def verify(manifest_file, harness_file):
    manifest, manifest_sha = read(manifest_file)
    harness_path = Path(harness_file).resolve()
    require(harness_path.is_file() and not harness_path.is_symlink(), "R4_HARNESS_REQUIRED")
    harness_sha = digest(harness_path)
    require(manifest.get("prepared") is True and manifest.get("repository") == str(ROOT)
            and manifest.get("fixture") == "tests/fixtures/native-first-canary"
            and manifest.get("shared_mcp_creation_claimed") is False
            and manifest.get("harness_sha256") == harness_sha,
            "EXACT_ORIGINAL_FIXTURE_MANIFEST_AND_R4_HARNESS_REQUIRED")
    fixture = ROOT / manifest["fixture"]
    require(fixture.is_dir() and not fixture.is_symlink(), "EXACT_NATIVE_FIXTURE_DIRECTORY_REQUIRED")
    records = manifest.get("files", [])
    require(len(records) == 101, "EXACT_NATIVE_FIXTURE_FILE_COUNT_REQUIRED")
    for record in records:
        relative = str(record.get("path") or "")
        require(relative.startswith("tests/fixtures/native-first-canary/")
                and (relative.endswith(".txt") or relative.endswith("trusted-build.js")),
                "R4_FIXTURE_MANIFEST_PATH_INVALID")
        file = (ROOT / relative).resolve()
        require(file.is_file() and not file.is_symlink() and file.is_relative_to(ROOT)
                and file.stat().st_size == int(record["size_bytes"]) and digest(file) == record["sha256"],
                "R4_FIXTURE_SEED_CHANGED")
    artifact = fixture / "build-artifact.txt"
    require(not artifact.exists(), "R4_BUILD_ARTIFACT_ALREADY_EXISTS")
    receipt = {
        "schema_version": 1, "operation": "r4_fixture_reuse_preparation", "ok": True,
        "observed_at_ms": int(time.time() * 1000), "repository": str(ROOT),
        "fixture": manifest["fixture"], "manifest_path": str(Path(manifest_file).resolve()),
        "manifest_sha256": manifest_sha, "harness_path": str(harness_path), "harness_sha256": harness_sha,
        "fixture_file_count": len(records), "build_artifact_absent": True,
        "shared_mcp_creation_claimed": False, "mutations": 0,
        "source_scope": "r4 wrapper input validation only; no fixture write or shared MCP claim",
    }
    return receipt


def write_receipt(receipt, output):
    output_path = Path(output)
    require(output_path.is_absolute() and output_path.parent.resolve() == Path(__file__).resolve().parent
            and not output_path.exists(), "NEW_R4_REUSE_RECEIPT_REQUIRED")
    with output_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(receipt, handle, indent=2)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--harness", default=str(Path(__file__).with_name("run-native-first-canary.py")))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = verify(args.manifest, args.harness)
    write_receipt(result, args.output)
    print(json.dumps({"operation": result["operation"], "ok": True, "receipt_path": args.output,
                      "manifest_sha256": result["manifest_sha256"], "harness_sha256": result["harness_sha256"]}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"operation": "r4_fixture_reuse_preparation", "ok": False,
                          "code": str(error) if isinstance(error, RuntimeError) else type(error).__name__}))
        sys.exit(1)
