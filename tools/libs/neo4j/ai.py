from time import sleep

import docker

from settings import LOGGER
from utils.rand import get_rand_string

START_STRING = "Remote interface available"


def import_csv_files(db_path, import_dir):
    docker_cli = docker.from_env()
    cname = "neo4j-v3-%s" % get_rand_string(5, special=False)
    LOGGER.info("Starting %s..." % cname)

    container = docker_cli.containers.run(
        "neo4j-ai:latest",
        name=cname,
        environment={
            "NEO4J_dbms_memory_pagecache_size": "2G",
            "NEO4J_dbms_memory_heap_max__size": "2G",
            "NEO4J_dbms_allow__upgrade": "true",
            "NEO4J_dbms_shell_enabled": "true",
            "NEO4J_AUTH": "none"
        },
        ports={
            "7474": "7474",
            "7687": "7687",
        },
        volumes={
            db_path: {"bind": "/data/databases/neo4j_v3.db", "mode": "rw"},
            import_dir: {"bind": "/var/lib/neo4j/import", "mode": "rw"}
        },
        detach=True
    )

    while START_STRING not in container.logs(tail=100):
        sleep(1)

    LOGGER.info("%s fully started." % cname)

    container.exec_run(
        """
        ./bin/neo4j-admin import --database=neo4j_v3.db --delimiter='TAB'
            --nodes=./import/nodes.csv --relationships=./import/edges.csv    
        """
    )

    LOGGER.info("%s fully imported." % cname)
    container.stop()


def start_container(db_path):
    docker_cli = docker.from_env()
    # neo_db_path = join(code_path, "neo4j_v3.db")
    cname = "neo4j-v3-%s" % get_rand_string(5, special=False)
    LOGGER.info("Starting %s..." % cname)

    container = docker_cli.containers.run(
        "neo4j-ai:latest",
        name=cname,
        environment={
            "NEO4J_dbms_memory_pagecache_size": "2G",
            "NEO4J_dbms_memory_heap_max__size": "2G",
            "NEO4J_dbms_allow__upgrade": "true",
            "NEO4J_dbms_shell_enabled": "true",
            "NEO4J_AUTH": "none"
        },
        ports={
            "7474": "7474",
            "7687": "7687",
        },
        volumes={
            db_path: {"bind": "/data/databases/graph.db", "mode": "rw"}
        },
        detach=True
    )

    while START_STRING not in container.logs(tail=100):
        sleep(1)

    LOGGER.info("%s fully started." % cname)
    container.stop()
