from __future__ import annotations

import hashlib
import json
import marshal
import sys
from typing import Any

from .build_verify import verify_build as run_build_verification


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
        }
        components = {
            name: hashlib.sha256(marshal.dumps(target.__code__)).hexdigest()
            for name, target in targets.items()
        }
        encoded = json.dumps(components, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return {
            "schema_version": 1,
            "algorithm": "sha256_python_marshal_code",
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "fingerprint": hashlib.sha256(encoded).hexdigest(),
            "components": components,
        }
