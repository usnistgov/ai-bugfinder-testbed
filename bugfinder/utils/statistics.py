""" Utilities for statistic purposes.
"""
from time import time


def get_time():
    return int(round(time() * 1000))


def has_better_metrics(eval_keys, current_metrics, last_metrics=None):
    if last_metrics is None:
        return True

    for eval_key in eval_keys:
        if last_metrics[eval_key] > current_metrics[eval_key]:
            return False

    return True
