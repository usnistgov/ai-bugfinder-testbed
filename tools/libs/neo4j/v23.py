# from os.path import join
from time import sleep

import docker

from settings import LOGGER
from utils.rand import get_rand_string

START_STRING = "Remote interface ready"


def main(db_path):
    docker_cli = docker.from_env()
    cname = "neo4j-v2-%s" % get_rand_string(5, special=False)
    # neo4j_v2_db_path = join(code_path, "neo4j_v2.db")

    LOGGER.info("Starting %s container..." % cname)

    neo4j2_container = docker_cli.containers.run(
        "neo4j:2.3.12",
        name=cname,
        environment={
            "NEO4J_CACHE_MEMORY": "2048M",
            "NEO4J_HEAP_MEMORY": "2048",
            "NEO4J_ALLOW_STORE_UPGRADE": "true",
            "NEO4J_AUTH": "none"
        },
        ports={"7474": "7474"},
        volumes={
            db_path: {"bind": "/data/graph.db", "mode": "rw"}
        },
        detach=True
    )

    while START_STRING not in neo4j2_container.logs(tail=100):
        sleep(1)

    LOGGER.info("%s fully converted." % cname)
    neo4j2_container.stop()
