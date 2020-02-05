""" Utilities using random generators
"""
import unittest
import string
from bugfinder.utils.rand import get_rand_string, NB_CHARS, SP_CHARS


class TestGetRandString(unittest.TestCase):
    def test_string_length_is_correct(self):
        self.assertEqual(len(get_rand_string(5)), 5)

    def test_all_false_throws_error(self):
        with self.assertRaises(IndexError):
            get_rand_string(5, False, False, False, False)

    def test_no_lower_returns_correct_string(self):
        self.assertNotIn(
            string.ascii_lowercase,
            get_rand_string(5, False, True, True, True)
        )

    def test_no_upper_returns_correct_string(self):
        self.assertNotIn(
            string.ascii_uppercase,
            get_rand_string(5, True, False, True, True)
        )

    def test_no_numbers_returns_correct_string(self):
        self.assertNotIn(
            NB_CHARS,
            get_rand_string(5, True, True, False, True)
        )

    def test_no_specials_returns_correct_string(self):
        self.assertNotIn(
            SP_CHARS,
            get_rand_string(5, True, True, True, False)
        )
