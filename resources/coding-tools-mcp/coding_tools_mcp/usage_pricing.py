from __future__ import annotations

import re
from typing import Any


PRICING_COMPONENTS = ("input", "output", "cached", "cache_creation", "reasoning")
PRICING_REVISION = "coding-tools-usage-pricing-2026-09-01-v1"


def _price(input_usd: float, output_usd: float, **extra: float) -> dict[str, float]:
    entry: dict[str, float] = {"input": input_usd, "output": output_usd}
    for component, rate in extra.items():
        if component in PRICING_COMPONENTS and rate is not None and rate >= 0:
            entry[component] = rate
    return entry


MODEL_PRICING: dict[str, dict[str, float]] = {
    "deepseek-v4-flash": _price(0.28, 0.42, cached=0.028),
    "deepseek-v4-pro": _price(0.28, 0.42, cached=0.028),
    "gpt-5.4-mini": _price(0.15, 0.6),
    "gpt-5.6-luna": _price(0.15, 0.6),
    "gpt-5.6-terra": _price(2.5, 10),
    "gpt-5.6-sol": _price(10, 40),
}

PATTERN_PRICING: list[tuple[re.Pattern[str], dict[str, float]]] = [
    (re.compile(r"^deepseek-"), MODEL_PRICING["deepseek-v4-flash"]),
]


def price_of(model: str, component: str) -> float | None:
    if component not in PRICING_COMPONENTS:
        return None
    normalized = str(model or "").strip()
    if not normalized:
        return None
    for name, entry in MODEL_PRICING.items():
        if normalized == name or normalized.endswith("/" + name):
            return entry.get(component)
    for pattern, entry in PATTERN_PRICING:
        if pattern.search(normalized):
            return entry.get(component)
    return None


def _token_count(usage: dict[str, Any], *keys: str) -> int:
    for key in keys:
        if key not in usage:
            continue
        value = usage.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return 0
        return max(0, int(value))
    return 0


def derive_cost(usage: dict[str, Any], model: str) -> tuple[float, dict[str, float]] | None:
    """Price canonical, non-overlapping token categories or fail closed."""
    input_total = _token_count(usage, "input_total_tokens", "input_tokens")
    input_cached = _token_count(usage, "input_cached_tokens", "cached_input_tokens")
    input_cache_creation = _token_count(usage, "input_cache_creation_tokens", "cache_write_tokens")
    if "input_uncached_tokens" in usage or "uncached_input_tokens" in usage:
        input_uncached = _token_count(usage, "input_uncached_tokens", "uncached_input_tokens")
    else:
        input_uncached = max(0, input_total - input_cached - input_cache_creation)

    output_total = _token_count(usage, "output_total_tokens", "output_tokens")
    output_reasoning = min(
        output_total,
        _token_count(usage, "output_reasoning_tokens", "reasoning_output_tokens"),
    )
    if "output_nonreasoning_tokens" in usage:
        output_nonreasoning = min(output_total, _token_count(usage, "output_nonreasoning_tokens"))
    else:
        output_nonreasoning = max(0, output_total - output_reasoning)

    priced: dict[str, float] = {}
    input_rate = price_of(model, "input")
    cached_rate = price_of(model, "cached")
    cache_creation_rate = price_of(model, "cache_creation")
    output_rate = price_of(model, "output")
    reasoning_rate = price_of(model, "reasoning")

    for component, tokens, rate in (
        ("input", input_uncached, input_rate),
        ("cached", input_cached, cached_rate),
        ("cache_creation", input_cache_creation, cache_creation_rate),
    ):
        if tokens <= 0:
            continue
        if rate is None:
            return None
        priced[component] = tokens * rate / 1_000_000

    if output_total > 0:
        if reasoning_rate is not None and output_reasoning > 0:
            if output_nonreasoning > 0:
                if output_rate is None:
                    return None
                priced["output"] = output_nonreasoning * output_rate / 1_000_000
            priced["reasoning"] = output_reasoning * reasoning_rate / 1_000_000
        else:
            if output_rate is None:
                return None
            priced["output"] = output_total * output_rate / 1_000_000
    if not priced:
        return None
    return round(sum(priced.values()), 9), priced