#!/usr/bin/env python3
"""Bind one verified release identity to the protected service configuration.

This helper is deliberately limited to the two operator-owned files that carry
the release revision and package fingerprint.  It never reads or prints secret
values, changes the ``current`` symlink, reloads systemd, restarts a service,
changes admission, or touches SQLite.  The caller must still perform those
operations through the reviewed deployment procedure.

The two files are prepared together: both temporary files are written and
validated before either destination is replaced.  If replacing the second
destination fails, the first destination is restored from its original bytes.
This closes the failure mode where ``control-plane.env`` retains an old
fingerprint while a systemd drop-in points at a newer release.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Iterable


REVISION_PATTERN = re.compile(r"^[0-9a-f]{40,64}$")
FINGERPRINT_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
REVISION_KEY = "CONTROL_PLANE_DECLARED_SOURCE_REVISION"
FINGERPRINT_KEY = "CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256"


class ActivationConfigError(ValueError):
    """The selected release or protected configuration is not safe to edit."""


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ActivationConfigError(f"cannot read protected configuration: {path}") from error


def _read_manifest(release_dir: Path) -> tuple[str, str, str]:
    manifest_path = release_dir / "release-manifest.json"
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ActivationConfigError("release manifest is missing or invalid") from error
    if not isinstance(payload, dict):
        raise ActivationConfigError("release manifest must be an object")
    source_revision = payload.get("source_revision")
    package_fingerprint = payload.get("package_source_sha256")
    release_name = payload.get("release_name")
    if (
        not isinstance(source_revision, str)
        or not REVISION_PATTERN.fullmatch(source_revision)
        or not isinstance(package_fingerprint, str)
        or not FINGERPRINT_PATTERN.fullmatch(package_fingerprint)
        or not isinstance(release_name, str)
        or not release_name
    ):
        raise ActivationConfigError("release manifest identity is invalid")
    return source_revision, package_fingerprint, release_name


def _ensure_final_newline(text: str) -> str:
    return text if text.endswith(("\n", "\r")) else text + "\n"


def _replace_key(text: str, key: str, value: str, *, environment: bool) -> str:
    """Replace exactly one key while preserving comments and line endings."""

    lines = text.splitlines(keepends=True)
    matches: list[int] = []
    for index, line in enumerate(lines):
        body = line.rstrip("\r\n")
        if environment:
            matches.append(index) if re.fullmatch(rf"\s*{re.escape(key)}=.*", body) else None
        else:
            matches.append(index) if re.fullmatch(rf"\s*Environment={re.escape(key)}=.*", body) else None
    if len(matches) > 1:
        raise ActivationConfigError(f"protected configuration contains duplicate {key}")
    prefix = "" if environment else "Environment="
    replacement = f"{prefix}{key}={value}"
    if matches:
        index = matches[0]
        newline = "\r\n" if lines[index].endswith("\r\n") else "\n" if lines[index].endswith("\n") else ""
        lines[index] = replacement + newline
        return "".join(lines)
    if not environment and "[Service]" not in {line.strip() for line in lines}:
        raise ActivationConfigError("systemd drop-in has no [Service] section")
    return _ensure_final_newline(text) + replacement + "\n"


def _mode(path: Path, default: int = 0o600) -> int:
    try:
        return stat.S_IMODE(path.stat().st_mode)
    except OSError:
        return default


def _temporary_bytes(path: Path, content: bytes, mode: int) -> Path:
    if not path.parent.is_dir():
        raise ActivationConfigError(f"protected configuration directory is missing: {path.parent}")
    descriptor, raw_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(raw_path)
    try:
        if hasattr(os, "fchmod"):
            os.fchmod(descriptor, mode)
        else:
            os.chmod(temporary, mode)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        return temporary
    except Exception:
        if descriptor >= 0:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)
        raise


def _replace_with_restore(path: Path, original: bytes, replacement: Path, mode: int) -> None:
    os.replace(replacement, path)
    try:
        os.chmod(path, mode)
    except OSError:
        # The replacement has already been committed.  Propagate the error so
        # the caller does not claim a fully prepared configuration.
        raise


def _restore(path: Path, original: bytes, mode: int) -> None:
    temporary = _temporary_bytes(path, original, mode)
    try:
        os.replace(temporary, path)
        os.chmod(path, mode)
    finally:
        temporary.unlink(missing_ok=True)


def prepare_activation_config(
    *,
    release_dir: Path,
    env_file: Path,
    drop_in: Path,
    check_only: bool = False,
) -> dict[str, object]:
    source_revision, package_fingerprint, release_name = _read_manifest(release_dir.resolve())
    original_env = env_file.read_bytes()
    original_drop_in = drop_in.read_bytes()
    env_text = original_env.decode("utf-8")
    drop_in_text = original_drop_in.decode("utf-8")
    expected_env = _replace_key(env_text, REVISION_KEY, source_revision, environment=True)
    expected_env = _replace_key(expected_env, FINGERPRINT_KEY, package_fingerprint, environment=True)
    expected_drop_in = _replace_key(drop_in_text, REVISION_KEY, source_revision, environment=False)
    expected_drop_in = _replace_key(expected_drop_in, FINGERPRINT_KEY, package_fingerprint, environment=False)
    env_bytes = expected_env.encode("utf-8")
    drop_in_bytes = expected_drop_in.encode("utf-8")
    env_matches = env_bytes == original_env
    drop_in_matches = drop_in_bytes == original_drop_in
    receipt: dict[str, object] = {
        "operation": "control_plane_activation_config_check" if check_only else "control_plane_activation_config_prepare",
        "release_name": release_name,
        "source_revision": source_revision,
        "package_source_sha256": package_fingerprint,
        "environment_matches": env_matches,
        "drop_in_matches": drop_in_matches,
        "changed": not (env_matches and drop_in_matches),
    }
    if check_only or (env_matches and drop_in_matches):
        return receipt

    env_mode = _mode(env_file)
    drop_in_mode = _mode(drop_in)
    env_temporary = _temporary_bytes(env_file, env_bytes, env_mode)
    drop_in_temporary = _temporary_bytes(drop_in, drop_in_bytes, drop_in_mode)
    env_replaced = False
    try:
        _replace_with_restore(env_file, original_env, env_temporary, env_mode)
        env_replaced = True
        try:
            _replace_with_restore(drop_in, original_drop_in, drop_in_temporary, drop_in_mode)
        except Exception as error:
            try:
                _restore(env_file, original_env, env_mode)
            except Exception as restore_error:
                raise ActivationConfigError("configuration update failed and rollback failed") from restore_error
            raise ActivationConfigError("configuration update rolled back after drop-in failure") from error
    finally:
        env_temporary.unlink(missing_ok=True)
        drop_in_temporary.unlink(missing_ok=True)
    receipt["environment_matches"] = True
    receipt["drop_in_matches"] = True
    receipt["changed"] = True
    return receipt


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-dir", required=True, help="verified extracted release directory")
    parser.add_argument("--env-file", required=True, help="protected control-plane.env")
    parser.add_argument("--drop-in", required=True, help="protected systemd immutable-release drop-in")
    parser.add_argument("--check-only", action="store_true", help="verify both files without writing")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        receipt = prepare_activation_config(
            release_dir=Path(args.release_dir),
            env_file=Path(args.env_file),
            drop_in=Path(args.drop_in),
            check_only=args.check_only,
        )
    except (ActivationConfigError, OSError, UnicodeError) as error:
        print(json.dumps({"error": {"code": "CONTROL_PLANE_ACTIVATION_CONFIG_FAILED", "message": str(error)}}))
        return 2
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
