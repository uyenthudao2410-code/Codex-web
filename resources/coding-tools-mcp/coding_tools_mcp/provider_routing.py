from __future__ import annotations

import hashlib
import json
from typing import Any


SIDE_EFFECT_CLASSES = frozenset({
    "read_only",
    "proposed_change",
    "deterministic_mutation",
    "consequential_mutation",
})
SCOPES = frozenset({"localized", "bounded", "broad"})
AMBIGUITIES = frozenset({"low", "medium", "high"})
EVIDENCE_QUALITIES = frozenset({"localized", "partial", "sparse"})
RISKS = frozenset({"low", "medium", "high", "critical"})
LATENCY_PRIORITIES = frozenset({"low", "normal", "high"})


def _enum(features: dict[str, Any], name: str, allowed: frozenset[str], default: str) -> str:
    value = str(features.get(name) or default).strip().lower()
    if value not in allowed:
        raise ValueError(f"{name} must be one of: {', '.join(sorted(allowed))}")
    return value


def normalize_shadow_route_features(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("shadow route features must be an object")
    allowed = {
        "side_effect_class",
        "scope",
        "ambiguity",
        "evidence_quality",
        "risk",
        "latency_priority",
        "hard_reasoning",
        "strong_oracle",
    }
    unexpected = sorted(set(value) - allowed)
    if unexpected:
        raise ValueError("unsupported shadow route feature fields: " + ", ".join(unexpected[:5]))
    for name in ("hard_reasoning", "strong_oracle"):
        if name in value and not isinstance(value[name], bool):
            raise ValueError(f"{name} must be boolean")
    return {
        "side_effect_class": _enum(value, "side_effect_class", SIDE_EFFECT_CLASSES, "read_only"),
        "scope": _enum(value, "scope", SCOPES, "bounded"),
        "ambiguity": _enum(value, "ambiguity", AMBIGUITIES, "medium"),
        "evidence_quality": _enum(value, "evidence_quality", EVIDENCE_QUALITIES, "partial"),
        "risk": _enum(value, "risk", RISKS, "medium"),
        "latency_priority": _enum(value, "latency_priority", LATENCY_PRIORITIES, "normal"),
        "hard_reasoning": bool(value.get("hard_reasoning", False)),
        "strong_oracle": bool(value.get("strong_oracle", False)),
    }


def recommend_shadow_route(value: Any) -> dict[str, Any]:
    features = normalize_shadow_route_features(value)
    side_effect = features["side_effect_class"]
    scope = features["scope"]
    risk = features["risk"]
    ambiguity = features["ambiguity"]
    evidence = features["evidence_quality"]
    latency = features["latency_priority"]
    hard = features["hard_reasoning"]
    oracle = features["strong_oracle"]

    if risk in {"high", "critical"} or side_effect == "consequential_mutation":
        route = {
            "route": "controller_manual",
            "provider": None,
            "model": None,
            "execution_class": "manual_gate",
            "reason_code": "HIGH_RISK_REQUIRES_CONTROLLER_GATE",
        }
    elif side_effect == "deterministic_mutation":
        route = {
            "route": "mcp_deterministic",
            "provider": "mcp",
            "model": None,
            "execution_class": "deterministic",
            "reason_code": "DETERMINISTIC_MUTATION_PREFERS_MCP",
        }
    elif side_effect == "read_only" and scope == "broad" and hard:
        route = {
            "route": "opencode_read_only_pro",
            "provider": "opencode-go",
            "model": "opencode-go/deepseek-v4-pro",
            "execution_class": "read_only",
            "reason_code": "BROAD_READ_ONLY_HARD_REASONING",
        }
    elif side_effect == "read_only" and scope == "broad":
        route = {
            "route": "opencode_read_only_flash",
            "provider": "opencode-go",
            "model": "opencode-go/deepseek-v4-flash",
            "execution_class": "read_only",
            "reason_code": "BROAD_READ_ONLY_BREADTH",
        }
    elif scope == "localized" and oracle and ambiguity == "low":
        route = {
            "route": "codex_mini",
            "provider": "codex",
            "model": "gpt-5.4-mini",
            "execution_class": "candidate",
            "reason_code": "LOCALIZED_STRONG_ORACLE",
        }
    elif scope in {"localized", "bounded"} and ambiguity in {"low", "medium"} and evidence != "sparse" and not hard:
        route = {
            "route": "codex_luna",
            "provider": "codex",
            "model": "gpt-5.6-luna",
            "execution_class": "candidate",
            "reason_code": "BOUNDED_LEAF_REASONING",
        }
    elif scope == "bounded" and evidence == "localized" and latency != "high":
        route = {
            "route": "codex_terra",
            "provider": "codex",
            "model": "gpt-5.6-terra",
            "execution_class": "deep_read_or_proposal",
            "reason_code": "LOCALIZED_CROSS_FILE_EVIDENCE",
        }
    else:
        route = {
            "route": "controller_manual",
            "provider": None,
            "model": None,
            "execution_class": "manual_gate",
            "reason_code": "AMBIGUOUS_OR_UNCALIBRATED",
        }

    canonical = json.dumps(features, sort_keys=True, separators=(",", ":"))
    return {
        "schema_version": 1,
        "mode": "shadow_only",
        "features": features,
        "recommendation": route,
        "feature_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "automatic_dispatch": False,
        "mutation_allowed": False,
    }


def recommendation_id(*, run_id: str, wave_id: str, recommendation: dict[str, Any]) -> str:
    feature_hash = str(recommendation.get("feature_sha256") or "")
    return "shadow-route-" + hashlib.sha256(
        f"{run_id}\0{wave_id}\0{feature_hash}".encode("utf-8")
    ).hexdigest()[:40]
