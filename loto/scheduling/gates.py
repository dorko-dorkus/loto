"""Gate predicate utilities for the task scheduler.

These helpers produce simple predicate functions that examine an event
state and determine whether a particular gate has been cleared.  Gates
are pure functions – they perform no I/O and never mutate the provided
state.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

State = Mapping[str, Any]


def permit_gate() -> Callable[[State], bool]:
    """Return a predicate that is satisfied when a permit is granted.

    The predicate expects the current event ``state`` to contain a boolean
    ``"permit"`` flag indicating whether the required permit has been
    issued.  Missing or falsey values cause the predicate to evaluate to
    ``False``.
    """

    def predicate(state: State) -> bool:
        return bool(state.get("permit"))

    return predicate


def hold_point() -> Callable[[State], bool]:
    """Return a predicate that blocks while a hold point is active.

    The predicate examines the ``"hold"`` flag on ``state``; it is
    considered cleared when this flag is absent or ``False``.
    """

    def predicate(state: State) -> bool:
        return not state.get("hold", False)

    return predicate


def shared_isolation(key: str) -> Callable[[State], bool]:
    """Return a predicate requiring a shared isolation identified by ``key``.

    The event ``state`` is expected to expose an ``"isolations"`` collection
    – either a mapping or a set – describing the currently established
    isolations.  The predicate evaluates to ``True`` when ``key`` is present
    and truthy in that collection.
    """

    def predicate(state: State) -> bool:
        isolations = state.get("isolations")
        if isinstance(isolations, dict):
            return bool(isolations.get(key))
        if isinstance(isolations, set):
            return key in isolations
        if isolations is None:
            return False
        try:
            return key in isolations
        except TypeError:
            return False

    return predicate


def compose_gates(*preds: Callable[[State], bool]) -> Callable[[State], bool]:
    """Combine multiple gate predicates using logical AND.

    The returned predicate evaluates all ``preds`` against a given event
    ``state`` and returns ``True`` only if every predicate is satisfied.  If
    no predicates are supplied the combined gate always returns ``True``.
    """

    def combined(state: State) -> bool:
        return all(pred(state) for pred in preds)

    return combined
