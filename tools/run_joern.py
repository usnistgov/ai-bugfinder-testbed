""" Script running Joern and providing a Neo4j v3 DB
"""
from os.path import join, exists
from shutil import rmtree, copytree
from time import sleep

import docker
from docker.errors import APIError

from settings import ROOT_DIR, LOGGER
from utils.rand import get_rand_string

start_string_v2 = "Remote interface ready"
start_string_v3 = "Remote interface available"


def run_neo4j_v3():
    neo_db_path = join(code_path, "neo4j_v3.db")
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
            neo_db_path: {"bind": "/data/databases/graph.db", "mode": "rw"}
        },
        detach=True
    )

    while start_string_v3 not in container.logs(tail=100):
        sleep(1)

    LOGGER.info("%s fully started." % cname)
    container.stop()


def run_neo4j_v2():
    cname = "neo4j-v2-%s" % get_rand_string(5, special=False)
    neo4j_v2_db_path = join(code_path, "neo4j_v2.db")

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
            neo4j_v2_db_path: {"bind": "/data/graph.db", "mode": "rw"}
        },
        detach=True
    )

    while start_string_v2 not in neo4j2_container.logs(tail=100):
        sleep(1)

    LOGGER.info("%s fully converted." % cname)
    neo4j2_container.stop()


def run_joern_lite(version):
    joern_lite_cname = get_rand_string(10, special=False)

    LOGGER.info("Starting joern-lite:%s (%s)..." % (version, joern_lite_cname))

    try:
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


def run_joern_031():
    LOGGER.info("Starting Joern 0.3.1...")
    run_joern_lite("0.3.1")

    LOGGER.info("Joern database generated. Preparing update to Neo4j 2.3...")
    src = join(code_path, "joern.db")
    dest = join(code_path, "neo4j_v2.db")

    if exists(dest):
        LOGGER.debug("%s directory already exists. Removing..." % dest)
        rmtree(dest)

    copytree(src, dest)

    LOGGER.info("Database ready. Updating to Neo4j 2.3...")
    run_neo4j_v2()

    LOGGER.info(
        "Database updated to Neo4J 2.3. Preparing update to Neo4j 3.5..."
    )
    src = join(code_path, "neo4j_v2.db")
    dest = join(code_path, "neo4j_v3.db")

    if exists(dest):
        LOGGER.debug("%s directory already exists. Removing..." % dest)
        rmtree(dest)

    copytree(src, dest)

    LOGGER.info("Database ready. Updating to Neo4j 3.5...")
    run_neo4j_v3()


def run_joern_040():
    print("joern040")


def run_joern(version):
    """ Function to start Joern in any known version.

    :param version:
    :return:
    """
    joern_versions = {
        "0.3.1": run_joern_031,
        "0.4.0": run_joern_031
    }

    if version not in joern_versions.keys():
        return False

    joern_versions[version]()


if __name__ == "__main__":
    path = "./data/_cwe121_0500a"
    code_path = join(ROOT_DIR, path)
    joern_version = "0.3.1"
    port = 7474

    docker_cli = docker.from_env()
    run_joern(joern_version)
