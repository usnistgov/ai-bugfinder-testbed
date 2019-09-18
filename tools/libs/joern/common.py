""" Common functions to run Joern code analysis
"""
import docker

from tools.settings import LOGGER
from tools.utils.containers import start_container
from tools.utils.rand import get_rand_string


def run_joern_lite(version, code_path):
    joern_lite_cname = get_rand_string(10, special=False)

    LOGGER.info("Starting joern-lite:%s (%s)..." % (version, joern_lite_cname))

    try:
        start_container(
            image_name="joern-lite:%s" % version,
            container_name=joern_lite_cname,
            volumes={code_path: "/code"},
            detach=False
        )
    except Exception as exc:
        LOGGER.error(
            "An error occured while running %s: %s" %
            (joern_lite_cname, str(exc))
        )
        exit(1)

    LOGGER.info("Joern execution finished.")
