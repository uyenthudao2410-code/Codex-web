from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


SEMANTIC_GRAPH_SCHEMA_VERSION = 1
DEFAULT_GRAPH_RECORD_BUDGET = 100
MAX_GRAPH_RECORD_BUDGET = 200
DEFAULT_GRAPH_FILE_BUDGET = 24
MAX_GRAPH_FILE_BUDGET = 64
DEFAULT_GRAPH_FILE_BYTES = 64 * 1024
MAX_GRAPH_TOTAL_BYTES = 256 * 1024


def _bounded_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return min(max(parsed, minimum), maximum)


def _safe_relative_path(value: Any) -> str:
    path = str(value or "").strip().replace("\\", "/")
    candidate = Path(path)
    if (
        not path
        or "\x00" in path
        or candidate.is_absolute()
        or (len(path) >= 2 and path[1] == ":")
        or any(part == ".." for part in candidate.parts)
    ):
        return ""
    return path


def _is_test_path(path: str) -> bool:
    lowered = f"/{path.lower()}"
    name = Path(path).name.lower()
    return (
        "/test/" in lowered
        or "/tests/" in lowered
        or name.startswith("test_")
        or "_test." in name
        or ".test." in name
        or ".spec." in name
    )


def _relation_kind(value: Any) -> str:
    kind = str(value or "").strip().lower()[:120]
    if "definition" in kind:
        return "definition"
    if "reference" in kind:
        return "reference"
    if "import" in kind or "module" in kind:
        return "import"
    return "match"


def _stable_id(*parts: str) -> str:
    hasher = hashlib.sha256()
    for part in parts:
        encoded = part.encode("utf-8", errors="surrogatepass")
        hasher.update(len(encoded).to_bytes(8, "big"))
        hasher.update(encoded)
    return hasher.hexdigest()


class SemanticRepositoryGraph:
    """Bounded, derived semantic index; source files remain the only authority."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.expanduser().resolve(strict=True)
        self._records: dict[str, dict[str, Any]] = {}
        self._provider_name: str | None = None
        self._provider_version: str | None = None
        self._provider_available = False
        self._provider_reason = ""
        self._last_update: dict[str, Any] = {
            "refreshed_paths": 0,
            "retained_records": 0,
            "dropped_records": 0,
            "evicted_records": 0,
            "bytes_read": 0,
        }

    def _file_identity(self, relative: str, *, max_read_bytes: int) -> dict[str, Any] | None:
        safe = _safe_relative_path(relative)
        if not safe or max_read_bytes <= 0:
            return None
        try:
            path = (self.workspace / safe).resolve(strict=True)
            path.relative_to(self.workspace)
            if not path.is_file():
                return None
            size = path.stat().st_size
        except (OSError, RuntimeError, ValueError):
            return None

        allowed = max(1, int(max_read_bytes))
        hasher = hashlib.sha256()
        hasher.update(size.to_bytes(8, "big", signed=False))
        consumed = 0
        try:
            with path.open("rb") as handle:
                if size <= allowed:
                    while True:
                        chunk = handle.read(min(16 * 1024, allowed - consumed + 1))
                        if not chunk:
                            break
                        consumed += len(chunk)
                        if consumed > allowed:
                            return None
                        hasher.update(chunk)
                    complete = True
                    hash_kind = "full"
                else:
                    prefix = (allowed + 1) // 2
                    suffix = allowed - prefix
                    head = handle.read(prefix)
                    consumed += len(head)
                    hasher.update(b"prefix")
                    hasher.update(head)
                    if suffix:
                        handle.seek(max(0, size - suffix))
                        tail = handle.read(suffix)
                        consumed += len(tail)
                        hasher.update(b"suffix")
                        hasher.update(tail)
                    complete = False
                    hash_kind = "prefix_suffix"
        except OSError:
            return None
        return {
            "sha256": hasher.hexdigest(),
            "bytes": size,
            "read_bytes": consumed,
            "complete": complete,
            "hash_kind": hash_kind,
        }

    def _refresh_record(self, record: dict[str, Any]) -> None:
        identity = self._file_identity(
            str(record.get("path") or ""),
            max_read_bytes=int(record.get("identity_budget_bytes") or DEFAULT_GRAPH_FILE_BYTES),
        )
        if identity is None or identity["sha256"] != record.get("source_sha256"):
            record["current"] = False
            record["stale"] = True
            return
        record["stale"] = False
        record["current"] = True if identity["complete"] and record.get("source_hash_complete") is True else None

    @staticmethod
    def _public_record(record: dict[str, Any], *, distance: int | None = None) -> dict[str, Any]:
        result = {
            "symbol_id": record["symbol_id"],
            "file_id": record["file_id"],
            "path": record["path"],
            "symbol": record["symbol"],
            "kind": record["kind"],
            "line": record.get("line"),
            "column": record.get("column"),
            "provider": record["provider"],
            "provider_version": record.get("provider_version"),
            "confidence": record["confidence"],
            "completeness": record["completeness"],
            "source_sha256": record["source_sha256"],
            "source_hash_kind": record["source_hash_kind"],
            "source_bytes": record["source_bytes"],
            "current": record.get("current"),
            "stale": bool(record.get("stale")),
            "test_association": bool(record.get("test_association")),
        }
        if distance is not None:
            result["distance"] = distance
        return result

    def update(
        self,
        *,
        searches: list[dict[str, Any]],
        provider_status: dict[str, Any] | None = None,
        max_records: int = DEFAULT_GRAPH_RECORD_BUDGET,
        max_files: int = DEFAULT_GRAPH_FILE_BUDGET,
        max_total_bytes: int = MAX_GRAPH_TOTAL_BYTES,
        max_file_bytes: int = DEFAULT_GRAPH_FILE_BYTES,
    ) -> dict[str, Any]:
        provider = provider_status if isinstance(provider_status, dict) else {}
        self._provider_name = str(provider.get("provider") or "").strip()[:120] or None
        self._provider_version = str(provider.get("provider_version") or "").strip()[:120] or None
        self._provider_available = provider.get("available") is True
        self._provider_reason = str(provider.get("reason") or "").strip()[:240]

        record_budget = _bounded_int(max_records, default=DEFAULT_GRAPH_RECORD_BUDGET, minimum=1, maximum=MAX_GRAPH_RECORD_BUDGET)
        file_budget = _bounded_int(max_files, default=DEFAULT_GRAPH_FILE_BUDGET, minimum=1, maximum=MAX_GRAPH_FILE_BUDGET)
        total_budget = _bounded_int(max_total_bytes, default=MAX_GRAPH_TOTAL_BYTES, minimum=1024, maximum=MAX_GRAPH_TOTAL_BYTES)
        per_file_budget = _bounded_int(max_file_bytes, default=DEFAULT_GRAPH_FILE_BYTES, minimum=1024, maximum=DEFAULT_GRAPH_FILE_BYTES)

        candidates: list[dict[str, Any]] = []
        touched_paths: list[str] = []
        dropped = 0
        for search in searches if isinstance(searches, list) else []:
            if not isinstance(search, dict):
                continue
            query = str(search.get("query") or "").strip()[:500]
            engine = str(search.get("engine") or "").strip()[:160]
            semantic = engine.startswith("semantic:")
            source_provider = engine.split(":", 1)[1] if semantic and ":" in engine else "text_fallback"
            version = self._provider_version if semantic else "builtin-v1"
            matches = search.get("matches") if isinstance(search.get("matches"), list) else []
            for match in matches:
                if not isinstance(match, dict):
                    continue
                path = _safe_relative_path(match.get("path"))
                symbol = str(match.get("symbol") or query).strip()[:500]
                if not path or not symbol:
                    continue
                if path not in touched_paths:
                    if len(touched_paths) >= file_budget:
                        dropped += 1
                        continue
                    touched_paths.append(path)
                if len(candidates) >= record_budget:
                    dropped += 1
                    continue
                relation = _relation_kind(match.get("kind"))
                confidence = "high" if semantic and relation in {"definition", "reference", "import"} else ("medium" if semantic else "low")
                candidates.append({
                    "path": path,
                    "symbol": symbol,
                    "kind": relation,
                    "line": match.get("line") if isinstance(match.get("line"), int) and not isinstance(match.get("line"), bool) else None,
                    "column": match.get("column") if isinstance(match.get("column"), int) and not isinstance(match.get("column"), bool) else None,
                    "provider": source_provider[:120],
                    "provider_version": version,
                    "confidence": confidence,
                    "semantic": semantic,
                })

        retained = sum(1 for record in self._records.values() if record.get("path") not in set(touched_paths))
        if touched_paths:
            touched = set(touched_paths)
            self._records = {key: value for key, value in self._records.items() if value.get("path") not in touched}

        identities: dict[str, dict[str, Any]] = {}
        remaining = total_budget
        bytes_read = 0
        for path in touched_paths:
            if remaining <= 0:
                break
            read_budget = min(per_file_budget, remaining)
            identity = self._file_identity(path, max_read_bytes=read_budget)
            if identity is None:
                continue
            identity["identity_budget_bytes"] = read_budget
            identities[path] = identity
            consumed = int(identity.get("read_bytes") or 0)
            bytes_read += consumed
            remaining = max(0, remaining - consumed)

        for candidate in candidates:
            identity = identities.get(candidate["path"])
            if identity is None:
                dropped += 1
                continue
            semantic_complete = candidate["semantic"] is True
            source_complete = identity["complete"] is True
            completeness = "complete" if semantic_complete and source_complete else "partial"
            symbol_id = _stable_id(
                candidate["path"],
                candidate["symbol"],
                candidate["kind"],
                str(candidate.get("line") or ""),
                str(candidate.get("column") or ""),
                identity["sha256"],
            )
            record = {
                **candidate,
                "symbol_id": symbol_id,
                "file_id": _stable_id(candidate["path"], identity["sha256"]),
                "source_sha256": identity["sha256"],
                "source_hash_kind": identity["hash_kind"],
                "source_hash_complete": source_complete,
                "source_bytes": identity["bytes"],
                "identity_budget_bytes": int(identity["identity_budget_bytes"]),
                "completeness": completeness,
                "current": True if source_complete else None,
                "stale": False,
                "test_association": _is_test_path(candidate["path"]),
            }
            self._records[symbol_id] = record

        evicted = max(0, len(self._records) - MAX_GRAPH_RECORD_BUDGET)
        if evicted:
            for record_id in list(self._records)[:evicted]:
                self._records.pop(record_id, None)
            retained = max(0, retained - evicted)
            dropped += evicted

        self._last_update = {
            "refreshed_paths": len(identities),
            "retained_records": retained,
            "dropped_records": dropped,
            "evicted_records": evicted,
            "bytes_read": bytes_read,
        }
        return self.status()

    def _source_hash(self) -> str:
        hasher = hashlib.sha256()
        for record in sorted(self._records.values(), key=lambda item: item["symbol_id"]):
            for value in (record["symbol_id"], record["source_sha256"]):
                encoded = str(value).encode("ascii", errors="ignore")
                hasher.update(len(encoded).to_bytes(8, "big"))
                hasher.update(encoded)
        return hasher.hexdigest()

    def status(self, *, refresh: bool = False) -> dict[str, Any]:
        if refresh:
            for record in self._records.values():
                self._refresh_record(record)
        records = list(self._records.values())
        stale = sum(record.get("stale") is True for record in records)
        current = sum(record.get("current") is True for record in records)
        uncertain = sum(record.get("current") is None for record in records)
        fallback = sum(record.get("provider") == "text_fallback" for record in records)
        partial = any(record.get("completeness") != "complete" for record in records) or self._last_update["dropped_records"] > 0
        return {
            "schema_version": SEMANTIC_GRAPH_SCHEMA_VERSION,
            "read_only": True,
            "provider": self._provider_name,
            "provider_version": self._provider_version,
            "provider_available": self._provider_available,
            "provider_reason": self._provider_reason or None,
            "indexed_records": len(records),
            "current_records": current,
            "stale_records": stale,
            "uncertain_records": uncertain,
            "fallback_records": fallback,
            "completeness": "partial" if partial else "complete",
            "source_hash": self._source_hash(),
            "last_update": dict(self._last_update),
        }

    def resolve_symbols(self, query: str, budget: int = 20) -> list[dict[str, Any]]:
        needle = str(query or "").strip().lower()
        if not needle:
            return []
        limit = _bounded_int(budget, default=20, minimum=1, maximum=MAX_GRAPH_RECORD_BUDGET)
        matches = [record for record in self._records.values() if needle in str(record.get("symbol") or "").lower()]
        result: list[dict[str, Any]] = []
        for record in sorted(matches, key=lambda item: (item["path"], item.get("line") or 0, item["symbol_id"]))[:limit]:
            self._refresh_record(record)
            result.append(self._public_record(record))
        return result

    def references(self, symbol_id: str, budget: int = 20) -> list[dict[str, Any]]:
        seed = self._records.get(str(symbol_id or ""))
        if seed is None:
            return []
        limit = _bounded_int(budget, default=20, minimum=1, maximum=MAX_GRAPH_RECORD_BUDGET)
        symbol = str(seed.get("symbol") or "").lower()
        peers = [record for record in self._records.values() if record["symbol_id"] != seed["symbol_id"] and str(record.get("symbol") or "").lower() == symbol]
        result: list[dict[str, Any]] = []
        for record in sorted(peers, key=lambda item: (item["kind"] != "reference", item["path"], item.get("line") or 0))[:limit]:
            self._refresh_record(record)
            result.append(self._public_record(record))
        return result

    def related_tests(self, symbol_id: str, budget: int = 20) -> list[dict[str, Any]]:
        seed = self._records.get(str(symbol_id or ""))
        if seed is None:
            return []
        limit = _bounded_int(budget, default=20, minimum=1, maximum=MAX_GRAPH_RECORD_BUDGET)
        symbol = str(seed.get("symbol") or "").lower()
        rows = [record for record in self._records.values() if record.get("test_association") is True and str(record.get("symbol") or "").lower() == symbol]
        result: list[dict[str, Any]] = []
        for record in sorted(rows, key=lambda item: (item["path"], item.get("line") or 0))[:limit]:
            self._refresh_record(record)
            result.append(self._public_record(record))
        return result

    def impact(self, seed_symbols: list[str], depth: int = 1, budget: int = 40) -> dict[str, Any]:
        limit = _bounded_int(budget, default=40, minimum=1, maximum=MAX_GRAPH_RECORD_BUDGET)
        bounded_depth = _bounded_int(depth, default=1, minimum=0, maximum=3)
        seeds: list[str] = []
        for token in seed_symbols if isinstance(seed_symbols, list) else []:
            text = str(token or "").strip()
            if text in self._records:
                seeds.append(text)
                continue
            lowered = text.lower()
            seeds.extend(record["symbol_id"] for record in self._records.values() if str(record.get("symbol") or "").lower() == lowered)
        frontier = list(dict.fromkeys(seeds))
        visited: set[str] = set()
        rows: list[dict[str, Any]] = []
        truncated = False
        for distance in range(bounded_depth + 1):
            next_frontier: list[str] = []
            for record_id in frontier:
                if record_id in visited:
                    continue
                record = self._records.get(record_id)
                if record is None:
                    continue
                visited.add(record_id)
                self._refresh_record(record)
                rows.append(self._public_record(record, distance=distance))
                if len(rows) >= limit:
                    truncated = True
                    break
                symbol = str(record.get("symbol") or "").lower()
                path = str(record.get("path") or "")
                for peer in self._records.values():
                    if peer["symbol_id"] in visited:
                        continue
                    same_symbol = str(peer.get("symbol") or "").lower() == symbol
                    same_file = str(peer.get("path") or "") == path
                    if same_symbol or same_file:
                        next_frontier.append(peer["symbol_id"])
            if truncated:
                break
            frontier = list(dict.fromkeys(next_frontier))
            if not frontier:
                break
        return {
            "schema_version": SEMANTIC_GRAPH_SCHEMA_VERSION,
            "records": rows,
            "depth_requested": bounded_depth,
            "truncated": truncated,
            "completeness": "partial" if truncated or any(row["completeness"] != "complete" for row in rows) else "complete",
        }
