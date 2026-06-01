"""E6.2 chunk lifecycle policy errors."""

from __future__ import annotations


class LifecycleError(ValueError):
    """Base error for lifecycle policy violations."""


class InvalidStateTransitionError(LifecycleError):
    """Raised when a state transition is not allowed."""


class ApprovalRequiredError(LifecycleError):
    """Raised when VC cannot be queued without narration approval."""
