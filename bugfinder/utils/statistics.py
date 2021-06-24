""" Utilities for statistic purposes.
"""
from time import time


def divide(dividend, divisor):
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
    secs, msecs = divide(time_in_ms, 1000)

    if secs == 0:
        return "%dms" % msecs

    mins, secs = divide(secs, 60)

    if mins == 0:
        return "%d.%03ds" % (secs, msecs)

    hours, mins = divide(mins, 60)

    if hours == 0:
        return "%dm%02ds" % (mins, secs)

    days, hours = divide(hours, 24)

    if days == 0:
        return "%dh%02dm%02ds" % (hours, mins, secs)

    return "%d days %02dh%02dm%02ds" % (days, hours, mins, secs)


def has_better_metrics(eval_keys, current_metrics, last_metrics=None):
    if last_metrics is None:
        return True

    for eval_key in eval_keys:
        if last_metrics[eval_key] > current_metrics[eval_key]:
            return False

    return True
