from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Callable

from .orchestration_ledger import OrchestrationLedger, fingerprint_paths, utc_now


class ProofLedger:
    """Content-addressed proof registry backed by the orchestration ledger."""

    def __init__(self, workspace: Path, ledger: OrchestrationLedger) -> None:
        self.workspace = workspace.resolve(strict=False)
        self.ledger = ledger

    def fingerprint(
        self,
        *,
        stage_id: str,
        stage_version: str = "1",
        base_head: str = "",
        worktree_fp: str = "",
        contract_fp: str = "",
        input_paths: list[str] | None = None,
        config: dict[str, Any] | None = None,
        upstream_proof_ids: list[str] | None = None,
    ) -> str:
        path_fp = fingerprint_paths(self.workspace, input_paths or [])
        raw = {
            "stage_id": stage_id,
            "stage_version": stage_version,
            "base_head": base_head,
            "worktree_fp": worktree_fp,
            "contract_fp": contract_fp,
            "path_fp": path_fp,
            "config": config or {},
            "upstream_proof_ids": upstream_proof_ids or [],
        }
        return hashlib.sha256(
            json.dumps(raw, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()

    def cached_pass(self, *, stage_id: str, stage_version: str, input_fingerprint: str) -> dict[str, Any] | None:
        return self.ledger.find_cached_pass(
            stage_id=stage_id,
            stage_version=stage_version,
            input_fingerprint=input_fingerprint,
        )

    def record(
        self,
        *,
        run_id: str,
        wave_id: str,
        stage_id: str,
        input_fingerprint: str,
        status: str,
        stage_version: str = "1",
        command: str = "",
        started_at: str | None = None,
        finished_at: str | None = None,
        duration_ms: int = 0,
        exit_code: int | None = None,
        cache_hit: bool = False,
        upstream_proof_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        command_hash = hashlib.sha256(command.encode("utf-8", errors="replace")).hexdigest() if command else ""
        proof_id = self.ledger.record_proof(
            run_id=run_id,
            wave_id=wave_id,
            stage_id=stage_id,
            stage_version=stage_version,
            input_fingerprint=input_fingerprint,
            status=status,
            command_hash=command_hash,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            exit_code=exit_code,
            cache_hit=cache_hit,
            upstream_proof_ids=upstream_proof_ids,
            metadata=metadata,
        )
        self.ledger.append_event(
            run_id,
            wave_id=wave_id,
            event_type="proof_recorded",
            payload={
                "proof_id": proof_id,
                "stage_id": stage_id,
                "stage_version": stage_version,
                "input_fingerprint": input_fingerprint,
                "status": status,
                "duration_ms": duration_ms,
                "exit_code": exit_code,
                "cache_hit": cache_hit,
                "upstream_proof_ids": upstream_proof_ids or [],
            },
        )
        return proof_id

    def run_cached(
        self,
        *,
        run_id: str,
        wave_id: str,
        stage_id: str,
        input_fingerprint: str,
        runner: Callable[[], dict[str, Any]],
        stage_version: str = "1",
        command: str = "",
        upstream_proof_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], str]:
        lookup = self.ledger.proof_cache_lookup(
            stage_id=stage_id,
            stage_version=stage_version,
            input_fingerprint=input_fingerprint,
        )
        cached = lookup.get("source_proof") if lookup.get("hit") else None
        if cached is not None:
            cached_result = cached.get("metadata", {}).get("result") if isinstance(cached.get("metadata"), dict) else None
            source_proof_id = str(cached["proof_id"])
            source_run_id = str(cached.get("run_id") or "")
            source_wave_id = str(cached.get("wave_id") or "")
            same_wave = source_run_id == run_id and source_wave_id == wave_id
            proof_id = source_proof_id
            if not same_wave:
                receipt_upstreams = list(dict.fromkeys([
                    *(str(item) for item in (upstream_proof_ids or []) if str(item)),
                    source_proof_id,
                ]))
                receipt_metadata = {
                    **(metadata or {}),
                    "result": dict(cached_result) if isinstance(cached_result, dict) else {},
                    "proof_reuse": {
                        "source_proof_id": source_proof_id,
                        "source_run_id": source_run_id,
                        "source_wave_id": source_wave_id,
                        "cache_hit": True,
                        "executed": False,
                        "execution_duration_ms": 0,
                    },
                }
                proof_id = self.record(
                    run_id=run_id,
                    wave_id=wave_id,
                    stage_id=stage_id,
                    stage_version=stage_version,
                    input_fingerprint=input_fingerprint,
                    status="passed",
                    command=command,
                    duration_ms=0,
                    exit_code=cached.get("exit_code"),
                    cache_hit=True,
                    upstream_proof_ids=receipt_upstreams,
                    metadata=receipt_metadata,
                )
            result = dict(cached_result) if isinstance(cached_result, dict) else {}
            result.update({
                "ok": True,
                "status": "passed",
                "overall_status": result.get("overall_status", "passed"),
                "exit_code": cached.get("exit_code", result.get("exit_code", 0)),
                "duration_ms": 0,
                "cache_hit": True,
                "cache_saved_ms": max(0, int(cached.get("duration_ms") or 0)),
                "proof_cache_eligible": True,
                "proof_cache_miss_reason": None,
                "proof_cache_source_proof_id": source_proof_id,
                "proof_id": proof_id,
                "input_fingerprint": input_fingerprint,
            })
            self.ledger.append_event(
                run_id,
                wave_id=wave_id,
                event_type="proof_cache_hit",
                payload={
                    "stage_id": stage_id,
                    "stage_version": stage_version,
                    "input_fingerprint": input_fingerprint,
                    "source_proof_id": source_proof_id,
                    "proof_id": proof_id,
                    "reuse_receipt_created": not same_wave,
                },
            )
            return result, proof_id

        source_proof = lookup.get("source_proof") if isinstance(lookup.get("source_proof"), dict) else None
        miss_reason = str(lookup.get("reason") or "cold")
        self.ledger.append_event(
            run_id,
            wave_id=wave_id,
            event_type="proof_cache_miss",
            payload={
                "stage_id": stage_id,
                "stage_version": stage_version,
                "input_fingerprint": input_fingerprint,
                "reason": miss_reason,
                "source_proof_id": source_proof.get("proof_id") if source_proof else None,
                "source_stage_version": source_proof.get("stage_version") if source_proof else None,
            },
        )
        started_at = utc_now()
        started = time.monotonic()
        result = runner()
        duration_ms = int(result.get("duration_ms") or max(0, int((time.monotonic() - started) * 1000)))
        exit_code = result.get("exit_code")
        status = "passed" if result.get("ok", exit_code == 0) is not False and exit_code in {None, 0} else "failed"
        proof_id = self.record(
            run_id=run_id,
            wave_id=wave_id,
            stage_id=stage_id,
            stage_version=stage_version,
            input_fingerprint=input_fingerprint,
            status=status,
            command=command,
            started_at=started_at,
            finished_at=utc_now(),
            duration_ms=duration_ms,
            exit_code=exit_code,
            cache_hit=False,
            upstream_proof_ids=upstream_proof_ids,
            metadata={**(metadata or {}), "result": result},
        )
        decorated = dict(result)
        decorated["cache_hit"] = False
        decorated["proof_cache_eligible"] = True
        decorated["proof_cache_miss_reason"] = miss_reason
        decorated["proof_cache_source_proof_id"] = source_proof.get("proof_id") if source_proof else None
        decorated["proof_id"] = proof_id
        decorated["input_fingerprint"] = input_fingerprint
        return decorated, proof_id
