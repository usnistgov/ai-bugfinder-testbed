import docker
from docker.errors import APIError

from settings import LOGGER
from utils.containers import wait_log_display
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

    wait_log_display(container, START_STRING)

    LOGGER.info("%s fully started." % cname)

    container.exec_run(
        """
        ./bin/neo4j-admin import --database=neo4j_v3.db --delimiter='TAB'
            --nodes=./import/nodes.csv --relationships=./import/edges.csv    
        """
    )

    LOGGER.info("%s fully imported." % cname)
    container.stop()

    return cname


def enhance_markup(db_path):
    docker_cli = docker.from_env()
    cname = "neo4j-v3-%s" % get_rand_string(5, special=False)
    LOGGER.info("Starting %s..." % cname)

    neo4j3_container = docker_cli.containers.run(
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

    wait_log_display(neo4j3_container, START_STRING)

    LOGGER.info("%s started. Running commands..." % cname)
    for cmd in COMMANDS:
        try:
            start = get_time()
            neo4j3_container.exec_run("./bin/neo4j-shell -c \"%s\"" % cmd)
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
    neo4j3_container.stop()

    return cname


def start_container(db_path, stop_after_execution=True):
    docker_cli = docker.from_env()
    cname = "neo4j-v3-%s" % get_rand_string(5, special=False)
    LOGGER.info("Starting %s..." % cname)

    neo4j3_container = docker_cli.containers.run(
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

    wait_log_display(neo4j3_container, START_STRING)

    LOGGER.info("%s fully started." % cname)

    if stop_after_execution:
        neo4j3_container.stop()

    return cname