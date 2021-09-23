""" Utility for Docker containers
"""
from os.path import realpath

import docker
from time import sleep

from bugfinder.settings import LOGGER


def start_container(
    image_name,
    container_name,
    ports=None,
    volumes=None,
    environment=None,
    command=None,
    detach=True,
):
    LOGGER.debug(
        "Starting container '%s' (image '%s')..." % (container_name, image_name)
    )
    if volumes is None:
        volumes = {}

    # Get absolute path for volumes
    volumes_realpath = dict()
    for vol_key, vol_value in volumes.items():
        volumes_realpath[realpath(vol_key)] = vol_value
    volumes = volumes_realpath

    if ports is None:
        ports = {}

    if environment is None:
        environment = {}

    docker_cli = docker.from_env()

    extra_args = dict()
    if command is not None:
        extra_args["command"] = command

    run_result = docker_cli.containers.run(
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
        **extra_args,
    )

    docker_cli.close()
    return run_result


def wait_log_display(container, log_string, max_wait_time=300):
    """ """
    LOGGER.debug(
        "Waiting for container '%s' to display '%s' (max_wait_time=%d)..."
        % (container.name, log_string, max_wait_time)
    )

    max_sleep_time = min(max_wait_time - 1, 12)
    current_wait = 0

    while (
        log_string.encode("utf-8") not in container.logs(tail=10)
        and current_wait < max_wait_time
    ):
        current_wait += 1
        sleep(min(current_wait, max_sleep_time))


def stop_container_by_name(container_name):
    LOGGER.debug("Stopping container '%s'..." % container_name)
    docker_cli = docker.from_env()
    container = docker_cli.containers.get(container_name)

    container.stop()
    docker_cli.close()
