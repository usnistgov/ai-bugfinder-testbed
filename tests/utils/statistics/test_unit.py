""" Utilities for statistic purposes.
"""
import unittest
from time import sleep

from bugfinder.utils.statistics import get_time


class TestGetTime(unittest.TestCase):
    def test_time_is_in_millisecond(self):
        start_time = get_time()
        sleep(1)
        total_time = get_time() - start_time

        self.assertTrue(1500 > total_time > 500)
