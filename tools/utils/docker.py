""" Utility for Docker containers
"""
from time import sleep


def wait_log_display(container, log_string):
    while log_string not in container.logs(tail=100):
        sleep(1)
