"""Forward-only compact storage for idempotency summaries.

Legacy rows retain ``summary_json``. New large summaries use a versioned blob
while keeping the only analytics predicates as scalar columns.
"""

from __future__ import annotations

import json
import re
import zlib
from typing import Any, Callable, Mapping


PLAIN_JSON = "plain_json"
ZLIB_JSON = "zlib_json"
COMPRESSION_MIN_BYTES = 1024
SECRET_KEY_RE = re.compile(r"(authorization|credential|password|passwd|secret|token|api[_-]?key|private[_-]?key)", re.I)


def _json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def scalar_columns(summary: dict[str, Any]) -> tuple[str, int]:
    error_code = str(summary.get("error_code") or "")[:128]
    preflight = 1 if summary.get("workflow_patch_preflight") in {True, 1} else 0
    return error_code, preflight


def encode_summary(summary: dict[str, Any], *, sanitize: Callable[[Any], Any]) -> tuple[str, str, bytes | None, str, int]:
    normalized = sanitize(summary)
    if not isinstance(normalized, dict):
        raise ValueError("idempotency summary must sanitize to an object")
    text = _json(normalized)
    raw = text.encode("utf-8")
    error_code, preflight = scalar_columns(normalized)
    if len(raw) < COMPRESSION_MIN_BYTES:
        return text, PLAIN_JSON, None, error_code, preflight
    compressed = zlib.compress(raw)
    if len(compressed) >= len(raw):
        return text, PLAIN_JSON, None, error_code, preflight
    return "{}", ZLIB_JSON, compressed, error_code, preflight


def decode_summary(row: Mapping[str, Any]) -> dict[str, Any]:
    codec = str(row["summary_codec"] or PLAIN_JSON) if "summary_codec" in row.keys() else PLAIN_JSON
    if codec == PLAIN_JSON:
        value = json.loads(row["summary_json"] or "{}")
    elif codec == ZLIB_JSON:
        blob = row["summary_blob"] if "summary_blob" in row.keys() else None
        if blob is None:
            raise ValueError("compressed idempotency summary is missing its blob")
        value = json.loads(zlib.decompress(bytes(blob)).decode("utf-8"))
    else:
        raise ValueError(f"unsupported idempotency summary codec: {codec}")
    if not isinstance(value, dict):
        raise ValueError("idempotency summary must decode to an object")
    return value


def secret_key_findings(summary: dict[str, Any]) -> list[str]:
    findings: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                direct_secret = (
                    str(key).lower() != "fencing_token"
                    and SECRET_KEY_RE.search(str(key))
                    and isinstance(child, str)
                    and child != "[REDACTED]"
                )
                if direct_secret:
                    findings.add(str(key)[:200])
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(summary)
    return sorted(findings)
