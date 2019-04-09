""" Utilities using random generators
"""
import string
from random import choice


def get_rand_string(length, lower=True, upper=True, numbers=True, special=True):
    lc = string.ascii_lowercase
    uc = string.ascii_uppercase
    nb = "1234567890"
    sp = "!@#$%^&*()_+-="

    chars = ""
    chars += lc if lower else ""
    chars += uc if upper else ""
    chars += nb if numbers else ""
    chars += sp if special else ""

    return "".join(choice(chars) for _ in xrange(length))
