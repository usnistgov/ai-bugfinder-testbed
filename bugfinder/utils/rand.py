""" Utilities using random generators
"""
import string
from random import choice

NB_CHARS = "1234567890"
SP_CHARS = "!@#$%^&*()_+-="


def get_rand_string(length, lower=True, upper=True, numbers=True, special=True):
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    numbers_chars = NB_CHARS
    special_chars = SP_CHARS

    chars = ""
    chars += lowercase if lower else ""
    chars += uppercase if upper else ""
    chars += numbers_chars if numbers else ""
    chars += special_chars if special else ""

    return "".join(choice(chars) for _ in range(length))
