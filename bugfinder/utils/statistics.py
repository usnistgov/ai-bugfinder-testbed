""" Utilities for statistic purposes.
"""
from typing import List

from time import time


def divide(dividend, divisor):
    """Division function to return quotient and remainder"""
    quotient = int(dividend / divisor)
    remainder = dividend % divisor

    return quotient, remainder


def get_time():
    """Get current time in microseconds

    Returns:
        int: current time in ms
    """
    return int(round(time() * 1000))


def display_time(time_in_ms):
    """Display time in a human friendly manner."""
    secs, msecs = divide(time_in_ms, 1000)

    if secs == 0:
        return f"{msecs}ms"

    mins, secs = divide(secs, 60)

    if mins == 0:
        return f"{secs}.{msecs:03d}s"

    hours, mins = divide(mins, 60)

    if hours == 0:
        return f"{mins}m{secs:02d}s"

    days, hours = divide(hours, 24)

    if days == 0:
        return f"{hours}h{mins:02d}m{secs:02d}s"

    return f"{days} days {hours:02d}h{mins:02d}m{secs:02d}s"


def has_better_metrics(
    eval_keys: list[str],
    current_metrics: dict[str, float],
    last_metrics: dict[str, float] = None,
) -> bool:
    """Evaluate two metrics datastructure depending on a set of keys."""
    if last_metrics is None:
        return True

    for eval_key in eval_keys:
        if last_metrics[eval_key] > current_metrics[eval_key]:
            return False

    return True
