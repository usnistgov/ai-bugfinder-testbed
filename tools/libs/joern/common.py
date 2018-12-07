""" Common functions to run Joern code analysis
"""
import docker
from docker.errors import APIError

from settings import LOGGER
from utils.rand import get_rand_string


def run_joern_lite(version, code_path):
    joern_lite_cname = get_rand_string(10, special=False)

    LOGGER.info("Starting joern-lite:%s (%s)..." % (version, joern_lite_cname))

    try:
        docker_cli = docker.from_env()
        docker_cli.containers.run(
            "joern-lite:%s" % version,
            name=joern_lite_cname,
            volumes={
                code_path: {"bind": "/code", "mode": "rw"}
            },
            remove=True
        )
    except APIError as ae:
        LOGGER.error(
            "An error occured while running %s: %s" %
            (joern_lite_cname, ae.message)
        )

    LOGGER.info("Joern execution finished.")
