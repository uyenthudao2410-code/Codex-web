from __future__ import annotations

import hashlib
import json
import sys
import types
from typing import Any

from .build_verify import verify_build as run_build_verification


def _stable_code_constant(value: Any) -> Any:
    """Return a deterministic JSON value for every Python code constant type.

    ``marshal.dumps(code)`` is not a stable behavior identity: its encoding can
    change when strings become interned during ordinary runtime activity. The
    continuation fence needs semantic code identity, not interpreter marshal
    cache state.
    """
    if isinstance(value, types.CodeType):
        return {"code": _stable_code_payload(value)}
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return {"float_hex": value.hex()}
    if isinstance(value, complex):
        return {"complex_hex": [value.real.hex(), value.imag.hex()]}
    if isinstance(value, bytes):
        return {"bytes_hex": value.hex()}
    if isinstance(value, tuple):
        return {"tuple": [_stable_code_constant(item) for item in value]}
    if isinstance(value, frozenset):
        items = [_stable_code_constant(item) for item in value]
        return {
            "frozenset": sorted(
                items,
                key=lambda item: json.dumps(
                    item, ensure_ascii=True, sort_keys=True, separators=(",", ":")
                ),
            )
        }
    if value is Ellipsis:
        return {"ellipsis": True}
    raise TypeError(
        f"unsupported Python code constant for deterministic behavior identity: {type(value).__name__}"
    )


def _stable_code_payload(code: types.CodeType) -> dict[str, Any]:
    return {
        "argcount": code.co_argcount,
        "posonlyargcount": code.co_posonlyargcount,
        "kwonlyargcount": code.co_kwonlyargcount,
        "nlocals": code.co_nlocals,
        "stacksize": code.co_stacksize,
        "flags": code.co_flags,
        "code_hex": code.co_code.hex(),
        "exceptiontable_hex": getattr(code, "co_exceptiontable", b"").hex(),
        "consts": [_stable_code_constant(item) for item in code.co_consts],
        "names": list(code.co_names),
        "varnames": list(code.co_varnames),
        "freevars": list(code.co_freevars),
        "cellvars": list(code.co_cellvars),
        "name": code.co_name,
        "qualname": getattr(code, "co_qualname", code.co_name),
    }


def stable_python_code_sha256(code: types.CodeType) -> str:
    payload = _stable_code_payload(code)
    encoded = json.dumps(
        payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class RuntimeBehaviorIdentityMixin:
    """Loaded-code fingerprint used by the controlled activation receipt."""

    def _loaded_behavior_identity(self) -> dict[str, Any]:
        runtime_type = type(self)
        targets = {
            "provider_cost_attribution": runtime_type.ingest_provider_telemetry,
            "patch_preflight": runtime_type._preflight_patch_sequence,
            "verification_workdir": runtime_type.verify_build,
            "verification_runner": run_build_verification,
            "stale_reconciliation": runtime_type._maybe_reconcile_stale_orchestration,
            "routing_policy": runtime_type._select_agent_execution_route,
            "external_review_policy": runtime_type._maybe_agent_workflow_external_review,
            "committed_review": runtime_type.committed_review,
            "run_continuation_policy": runtime_type._run_continuation_grant,
            "run_continuation_driver": runtime_type._run_continuation_start_driver,
            "run_continuation_autoresume": runtime_type._run_continuation_try_auto_resume,
        }
        components = {
            name: stable_python_code_sha256(target.__code__)
            for name, target in targets.items()
        }
        encoded = json.dumps(components, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return {
            "schema_version": 2,
            "algorithm": "sha256_python_semantic_code_v2",
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "fingerprint": hashlib.sha256(encoded).hexdigest(),
            "components": components,
        }
