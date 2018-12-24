""" Utility for Docker containers
"""
from time import sleep

import docker


def wait_log_display(container, log_string):
    while log_string not in container.logs(tail=10):
        sleep(1)


def stop_container_by_name(container_name):
    docker_cli = docker.from_env()
    container = docker_cli.containers.get(container_name)

    container.stop()
