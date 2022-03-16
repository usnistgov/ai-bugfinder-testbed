""" Utilities for statistic purposes.
"""
import unittest
from time import sleep

from bugfinder.utils.statistics import get_time, display_time, has_better_metrics


class TestGetTime(unittest.TestCase):
    def test_time_is_in_millisecond(self):
        start_time = get_time()
        sleep(1)
        total_time = get_time() - start_time

        self.assertTrue(1500 > total_time > 500)


class TestDisplayTime(unittest.TestCase):
    def test_ms_display(self):
        self.assertEqual(display_time(123), "123ms")

    def test_secs_display(self):
        self.assertEqual(display_time(1234), "1.234s")

    def test_mins_display(self):
        self.assertEqual(display_time(83000), "1m23s")

    def test_hours_display(self):
        self.assertEqual(display_time(5025000), "1h23m45s")

    def test_days_display(self):
        self.assertEqual(display_time(95696000), "1 days 02h34m56s")


class TestHasBetterMetrics(unittest.TestCase):
    def test_last_metrics_none_returns_true(self):
        self.assertTrue(has_better_metrics([], {}, None))

    def test_key_not_in_current_metrics_raises_error(self):
        with self.assertRaises(KeyError):
            has_better_metrics(["key"], {}, {"key": 0})

    def test_key_not_in_last_metrics_raises_error(self):
        with self.assertRaises(KeyError):
            has_better_metrics(["key"], {"key": 0}, {})

    def test_better_current_metrics_returns_true(self):
        self.assertTrue(has_better_metrics(["key"], {"key": 1}, {"key": 0}))

    def test_better_last_metrics_returns_false(self):
        self.assertFalse(has_better_metrics(["key"], {"key": 0}, {"key": 1}))

    def test_better_equal_metrics_returns_true(self):
        self.assertTrue(has_better_metrics(["key"], {"key": 1}, {"key": 1}))
