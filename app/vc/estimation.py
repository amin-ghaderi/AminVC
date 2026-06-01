"""E5.0 VC progress time estimation."""

from __future__ import annotations


def elapsed_seconds_since(start_epoch: float, now_epoch: float) -> int:
    return max(0, int(now_epoch - start_epoch))


def estimate_remaining_seconds(
    current_step: int,
    total_steps: int,
    elapsed_seconds: int,
) -> int:
    """
    Average step duration × remaining steps.

    Unreliable for steps 0–1; returns 0 until current_step >= 2.
    """
    if current_step < 2:
        return 0
    remaining_steps = total_steps - current_step
    if remaining_steps <= 0:
        return 0
    avg_step_time = elapsed_seconds / current_step
    return int(avg_step_time * remaining_steps)


def progress_percent(current_step: int, total_steps: int) -> float:
    if total_steps <= 0:
        return 0.0
    return (current_step / total_steps) * 100.0
