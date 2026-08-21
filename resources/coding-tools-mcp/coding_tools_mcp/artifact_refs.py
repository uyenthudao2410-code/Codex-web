from __future__ import annotations

from typing import Any


ARTIFACT_REF_SCHEMA_VERSION = 1


def _text(value: Any, limit: int = 512) -> str:
    return str(value or "").strip()[:limit]


def build_artifact_ref(
    *,
    kind: str,
    scope: str,
    source: str,
    locator: dict[str, Any],
    retrieval: dict[str, Any] | None = None,
    durability: str,
    restart_safe: bool,
    content_addressed: bool,
    owner_run: str = "",
    owner_wave: str = "",
    size_bytes: int | None = None,
    sha256: str = "",
    mime: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a content-free locator for evidence retained outside model context."""
    result: dict[str, Any] = {
        "schema_version": ARTIFACT_REF_SCHEMA_VERSION,
        "kind": _text(kind, 100),
        "scope": _text(scope, 100),
        "source": _text(source, 100),
        "locator": dict(locator),
        "durability": _text(durability, 100),
        "restart_safe": bool(restart_safe),
        "content_addressed": bool(content_addressed),
    }
    if retrieval:
        result["retrieval"] = dict(retrieval)
    if owner_run:
        result["owner_run"] = _text(owner_run, 256)
    if owner_wave:
        result["owner_wave"] = _text(owner_wave, 256)
    if isinstance(size_bytes, int) and not isinstance(size_bytes, bool) and size_bytes >= 0:
        result["size_bytes"] = size_bytes
    if sha256:
        result["sha256"] = _text(sha256, 128)
    if mime:
        result["mime"] = _text(mime, 200)
    if extra:
        result.update(extra)
    return result


def command_output_artifact_ref(
    payload: dict[str, Any],
    *,
    owner_run: str = "",
    owner_wave: str = "",
) -> dict[str, Any] | None:
    command_id = _text(payload.get("command_id") or payload.get("session_id"), 256)
    raw_refs = payload.get("output_refs")
    refs = raw_refs if isinstance(raw_refs, dict) else {}
    raw_retention = payload.get("output_retention")
    retention = raw_retention if isinstance(raw_retention, dict) else {}
    streams: dict[str, Any] = {}

    for stream in ("stdout", "stderr"):
        output_ref = _text(refs.get(stream), 512)
        if not output_ref.startswith("command:"):
            continue
        raw_metrics = retention.get(stream)
        metrics = raw_metrics if isinstance(raw_metrics, dict) else {}

        def metric(name: str) -> int:
            value = metrics.get(name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return 0
            return max(0, int(value))

        streams[stream] = {
            "output_ref": output_ref,
            "total_stream_bytes": metric("total_stream_bytes"),
            "total_retained_bytes": metric("total_retained_bytes"),
            "head_retained_bytes": metric("head_retained_bytes"),
            "tail_retained_bytes": metric("tail_retained_bytes"),
            "evicted_gap_bytes": metric("evicted_gap_bytes"),
            "evicted_bytes_total": metric("evicted_bytes_total"),
        }
    if not command_id or not streams:
        return None
    size_bytes = sum(int(item.get("total_stream_bytes") or 0) for item in streams.values())
    return build_artifact_ref(
        kind="command_output",
        scope="runtime_retained",
        source="command",
        locator={"command_id": command_id},
        retrieval={"tool": "command_control", "action": "read"},
        durability="process_runtime",
        restart_safe=False,
        content_addressed=False,
        owner_run=owner_run,
        owner_wave=owner_wave,
        size_bytes=size_bytes,
        extra={"command_id": command_id, "streams": streams},
    )


def provider_result_artifact_ref(
    *,
    dispatch_id: str,
    run_id: str,
    wave_id: str,
    provider_id: str,
    model: str,
    result_chars: int,
    output_truncated: bool,
) -> dict[str, Any]:
    return build_artifact_ref(
        kind="provider_result",
        scope="runtime_retained",
        source=provider_id,
        locator={"dispatch_id": _text(dispatch_id, 256)},
        retrieval={"control_plane": "execution_hub", "action": "provider_observe"},
        durability="process_runtime",
        restart_safe=False,
        content_addressed=False,
        owner_run=run_id,
        owner_wave=wave_id,
        extra={
            "model": _text(model, 200),
            "result_chars": max(0, int(result_chars)),
            "output_truncated": bool(output_truncated),
        },
    )


def proof_artifact_ref(proof: dict[str, Any]) -> dict[str, Any] | None:
    proof_id = _text(proof.get("proof_id"), 256)
    run_id = _text(proof.get("run_id"), 256)
    if not proof_id or not run_id:
        return None
    return build_artifact_ref(
        kind="orchestration_proof",
        scope="orchestration_ledger",
        source="proof_ledger",
        locator={"proof_id": proof_id},
        retrieval={"tool": "task_control", "action": "audit", "run_id": run_id},
        durability="workspace_ledger",
        restart_safe=True,
        content_addressed=False,
        owner_run=run_id,
        owner_wave=_text(proof.get("wave_id"), 256),
        extra={
            "stage_id": _text(proof.get("stage_id"), 256),
            "stage_version": _text(proof.get("stage_version"), 128),
            "input_fingerprint": _text(proof.get("input_fingerprint"), 128),
            "status": _text(proof.get("status"), 64),
        },
    )


def handoff_capsule_artifact_ref(capsule: dict[str, Any]) -> dict[str, Any] | None:
    capsule_id = _text(capsule.get("capsule_id"), 256)
    run_id = _text(capsule.get("run_id"), 256)
    if not capsule_id or not run_id:
        return None
    raw_bytes = capsule.get("bytes")
    size_bytes = raw_bytes if isinstance(raw_bytes, int) and not isinstance(raw_bytes, bool) and raw_bytes >= 0 else None
    return build_artifact_ref(
        kind="handoff_capsule",
        scope="orchestration_ledger",
        source="handoff_ledger",
        locator={"capsule_id": capsule_id},
        retrieval={"tool": "task_control", "action": "handoff", "handoff_action": "get", "run_id": run_id},
        durability="workspace_ledger",
        restart_safe=True,
        content_addressed=True,
        owner_run=run_id,
        owner_wave=_text(capsule.get("wave_id"), 256),
        size_bytes=size_bytes,
        sha256=_text(capsule.get("sha256"), 128),
        extra={"status": _text(capsule.get("status"), 64)},
    )


def build_file_artifact_ref(
    artifact: dict[str, Any],
    *,
    hash_algorithm: str = "sha256",
    owner_run: str = "",
    owner_wave: str = "",
) -> dict[str, Any] | None:
    path = _text(artifact.get("path"), 2000)
    algorithm = _text(hash_algorithm, 32).lower() or "sha256"
    content_hash = _text(artifact.get(algorithm), 256)
    raw_size = artifact.get("size")
    size_bytes = raw_size if isinstance(raw_size, int) and not isinstance(raw_size, bool) and raw_size >= 0 else None
    if not path or not content_hash:
        return None
    return build_artifact_ref(
        kind="build_artifact",
        scope="workspace_file",
        source="build_verify",
        locator={"path": path},
        retrieval={"scheme": "workspace_path", "path": path},
        durability="workspace_file",
        restart_safe=True,
        content_addressed=True,
        owner_run=owner_run,
        owner_wave=owner_wave,
        size_bytes=size_bytes,
        sha256=content_hash if algorithm == "sha256" else "",
        extra={"hash_algorithm": algorithm, "content_hash": content_hash},
    )
