from __future__ import annotations

from typing import Any


class ControllerContinuityError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        category: str = "validation",
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.category = category
        self.retryable = retryable
        self.details = dict(details or {})


class ToolFailure(Exception):
    """A recoverable tool-domain failure that should be shown to the agent."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        category: str = "runtime",
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.category = category
        self.retryable = retryable
        self.details = details or {}


EXCEPTION_GROUP_CHILD_LIMIT = 8
EXCEPTION_GROUP_MESSAGE_LIMIT = 500


def normalize_exception_group(exc: BaseExceptionGroup) -> ToolFailure:
    """Convert an async exception group into bounded, structured tool evidence."""

    leaves: list[BaseException] = []

    def collect(value: BaseException) -> None:
        if isinstance(value, BaseExceptionGroup):
            for child in value.exceptions:
                collect(child)
            return
        leaves.append(value)

    collect(exc)
    children: list[dict[str, Any]] = []
    for leaf in leaves[:EXCEPTION_GROUP_CHILD_LIMIT]:
        if isinstance(leaf, ToolFailure):
            children.append({
                "type": type(leaf).__name__,
                "code": leaf.code,
                "category": leaf.category,
                "retryable": leaf.retryable,
                "message": leaf.message[:EXCEPTION_GROUP_MESSAGE_LIMIT],
            })
        else:
            children.append({
                "type": type(leaf).__name__,
                "message": str(leaf)[:EXCEPTION_GROUP_MESSAGE_LIMIT],
            })

    group_details = {
        "exception_group": True,
        "group_type": type(exc).__name__,
        "leaf_count": len(leaves),
        "children": children,
        "children_truncated": len(leaves) > EXCEPTION_GROUP_CHILD_LIMIT,
    }
    if len(leaves) == 1 and isinstance(leaves[0], ToolFailure):
        child = leaves[0]
        return ToolFailure(
            child.code,
            child.message,
            category=child.category,
            retryable=child.retryable,
            details={**child.details, **group_details},
        )

    retryable = bool(leaves) and all(
        isinstance(leaf, ToolFailure) and leaf.retryable
        for leaf in leaves
    )
    return ToolFailure(
        "ASYNC_TASK_GROUP_FAILED",
        "Concurrent runtime tasks failed; inspect the structured child failures.",
        category="runtime",
        retryable=retryable,
        details=group_details,
    )


class JsonRpcError(Exception):
    """A JSON-RPC protocol failure with an optional structured data payload."""

    def __init__(self, code: int, message: str, data: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data
