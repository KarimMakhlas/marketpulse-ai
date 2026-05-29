"""Langfuse observability shim.

Exposes `observe` — a decorator that is the real Langfuse `@observe` *only* when
Langfuse credentials are configured. Without credentials it is a genuine no-op.

Why this exists: importing `langfuse.observe` directly always succeeds when the
package is installed (it is), but the returned decorator initialises a disabled
client and logs `Authentication error: ... Client will be disabled` on *every*
decorated call. The Self-RAG pipeline decorates both the grader node and the
answer orchestrator, so an unconfigured local run spams that warning twice per
query. Resolving the decorator against credential presence keeps the no-op path
truly silent, as the docs promise.

Resolution happens once at import time. Entry points (`ui/app.py`,
`synthesis/__main__.py`) call `load_dotenv()` before importing anything that
imports this module, so the env vars are populated by the time we read them.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, Protocol, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])


class _IdentityDecorator(Protocol):
    """A decorator applied bare (`@observe`) that returns the function unchanged.

    Typing `observe` this way keeps `--strict`'s disallow_untyped_decorators
    happy: it preserves the decorated function's signature instead of erasing
    it to `Any` (which a raw runtime-resolved value would do).
    """

    def __call__(self, func: F, /) -> F: ...


def _noop_observe(func: Any = None, **_: Any) -> Any:
    """Transparent decorator supporting both `@observe` and `@observe(...)` forms."""
    if func is not None:
        return func
    return lambda f: f


def _langfuse_configured() -> bool:
    return bool(os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"))


def _resolve_observe() -> Any:
    if not _langfuse_configured():
        return _noop_observe
    # Credentials present — use the real decorator. The import moved from
    # `langfuse.decorators` (3.x) to top-level `langfuse` (4.x); try both.
    try:
        from langfuse import observe as real_observe

        return real_observe
    except ImportError:
        try:
            from langfuse.decorators import observe as real_observe  # type: ignore[no-redef]

            return real_observe
        except ImportError:
            return _noop_observe


observe: _IdentityDecorator = cast("_IdentityDecorator", _resolve_observe())
