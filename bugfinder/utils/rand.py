""" Utilities using random generators
"""
import string
from random import choice

NB_CHARS = "1234567890"
SP_CHARS = "!@#$%^&*()_+-="


def get_rand_string(length, lower=True, upper=True, numbers=True, special=True):
    lc = string.ascii_lowercase
    uc = string.ascii_uppercase
    nb = NB_CHARS
    sp = SP_CHARS

    chars = ""
    chars += lc if lower else ""
    chars += uc if upper else ""
    chars += nb if numbers else ""
    chars += sp if special else ""

    return "".join(choice(chars) for _ in range(length))
