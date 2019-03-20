""" Utilities for statistic purposes.
"""
from time import time


def get_time():
    return int(round(time() * 1000))
