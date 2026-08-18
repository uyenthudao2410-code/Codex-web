from __future__ import annotations

import re
from typing import Any


PRICING_COMPONENTS = ("input", "output", "cached", "cache_creation", "reasoning")


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


def derive_cost(usage: dict[str, Any], model: str) -> tuple[float, dict[str, float]] | None:
    priced: dict[str, float] = {}
    for component in PRICING_COMPONENTS:
        rate = price_of(model, component)
        if rate is None:
            continue
        count = usage.get(component + "_tokens", 0)
        if component == "cached":
            count = usage.get("cached_input_tokens", 0)
        if component == "cache_creation":
            count = usage.get("cache_write_tokens", 0)
        if component == "input":
            count = usage.get("uncached_input_tokens", usage.get("input_tokens", 0))
        tokens = max(0, int(count or 0))
        if tokens > 0:
            priced[component] = tokens * rate / 1_000_000
    if not priced:
        return None
    return round(sum(priced.values()), 9), priced