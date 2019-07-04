from os.path import join

import docker
from docker.errors import APIError
from py2neo import Graph

from settings import LOGGER, NEO4J_V3_MEMORY
from utils.containers import wait_log_display, stop_container_by_name
from utils.rand import get_rand_string
from utils.statistics import get_time


START_STRING = "Remote interface available"

COMMANDS = [
    "match (n) set n:GenericNode;",
    "create index on :GenericNode(type);",
    "create index on :GenericNode(filepath);",
    """
    match (root1:GenericNode)-[:FLOWS_TO|REACHES|CONTROLS]->()
    where root1.type in [ 
        'Condition', 'ForInit', 'IncDecOp',
        'ExpressionStatement', 'IdentifierDeclStatement', 'CFGEntryNode',
        'BreakStatement', 'Parameter', 'ReturnStatement', 'Label',
        'GotoStatement', 'Statement', 'UnaryExpression' 
    ]
    set root1:UpstreamNode;  
    """,
    """
    match ()-[:FLOWS_TO|REACHES|CONTROLS]->(root2:GenericNode)
    where root2.type in [
        'CFGExitNode', 'IncDecOp', 'Condition',
        'ExpressionStatement', 'ForInit', 'IdentifierDeclStatement',
        'BreakStatement', 'Parameter', 'ReturnStatement', 'Label',
        'GotoStatement', 'Statement', 'UnaryExpression' 
    ]
    set root2:DownstreamNode;
    """,
]


def import_csv_files(db_path, import_dir):
    db_path_import = "neo4j_v3.db"
    neo4j3_container, cname = start_container(db_path, db_bind_path=db_path_import,
                                              import_dir=import_dir)

    neo4j3_container.exec_run(
        """
        ./bin/neo4j-admin import --database=%s --delimiter='TAB'
            --nodes=/var/lib/neo4j/import/nodes.csv 
            --relationships=/var/lib/neo4j/import/edges.csv    
        """ % db_path_import
    )

    LOGGER.info("CSV file imported.")
    neo4j3_container.stop()

    return cname


def enhance_markup(db_path):
    neo4j3_container, cname = start_container(db_path)

    LOGGER.info("Running commands...")

    neo4j_db = Graph(
        scheme="http",
        host="0.0.0.0",
        port="7474"
    )

    for cmd in COMMANDS:
        try:
            start = get_time()
            # neo4j3_container.exec_run("./bin/neo4j-shell -c \"%s\"" % cmd)
            neo4j_db.run(cmd)
            end = get_time()

            LOGGER.info(
                "Command %d out of %d run in %dms" %
                (COMMANDS.index(cmd) + 1, len(COMMANDS), end - start)
            )
        except APIError as error:
            LOGGER.info(
                "An error occured while executing command: %s" %
                error.message
            )
            break

    LOGGER.info("%s fully converted." % cname)
    stop_container_by_name(cname)

    return cname


def start_container(db_path, db_bind_path="graph.db", import_dir=None, stop_after_execution=False):
    docker_cli = docker.from_env()
    cname = "neo4j-v3-%s" % get_rand_string(5, special=False)
    LOGGER.info("Starting %s..." % cname)

    neo4j3_container_volumes = {
        db_path: {"bind": join("/data/databases", db_bind_path), "mode": "rw"}
    }

    if import_dir is not None:
        neo4j3_container_volumes[import_dir] = {
            "bind": "/var/lib/neo4j/import",
            "mode": "rw"
        }

    neo4j3_container = docker_cli.containers.run(
        "neo4j-ai:latest",
        name=cname,
        environment={
            "NEO4J_dbms_memory_pagecache_size": NEO4J_V3_MEMORY,
            "NEO4J_dbms_memory_heap_max__size": NEO4J_V3_MEMORY,
            "NEO4J_dbms_allow__upgrade": "true",
            "NEO4J_dbms_shell_enabled": "true",
            "NEO4J_AUTH": "none"
        },
        ports={
            "7474": "7474",
            "7687": "7687",
        },
        volumes=neo4j3_container_volumes,
        detach=True
    )

    wait_log_display(neo4j3_container, START_STRING)

    LOGGER.info("%s started." % cname)

    if stop_after_execution:
        neo4j3_container.stop()

    return neo4j3_container, cname
