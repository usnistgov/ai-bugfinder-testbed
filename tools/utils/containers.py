""" Utility for Docker containers
"""
from time import sleep

import docker


def start_container(image_name, container_name, ports=None, volumes=None,
                    environment=None, command=None, detach=True):
    if volumes is None:
        volumes = {}

    if ports is None:
        ports = {}

    if environment is None:
        environment = {}

    docker_cli = docker.from_env()

    extra_args = dict()
    if command is not None:
        extra_args["command"] = command

    container = docker_cli.containers.run(
        image_name,
        name=container_name,
        environment=environment,
        ports=ports,
        volumes={
            local_dir: {"bind": cont_dir, "mode": "rw"}
            for local_dir, cont_dir in volumes.items()
        },
        detach=detach,
        remove=not detach,
        **extra_args
    )

    return container


def wait_log_display(container, log_string):
    while log_string.encode("utf-8") not in container.logs(tail=10):
        sleep(1)


def stop_container_by_name(container_name):
    docker_cli = docker.from_env()
    container = docker_cli.containers.get(container_name)

    container.stop()
