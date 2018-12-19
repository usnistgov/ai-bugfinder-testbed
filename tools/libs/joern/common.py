""" Common functions to run Joern code analysis
"""
import docker
from docker.errors import APIError

from libs.neo4j.ai import START_STRING
from settings import LOGGER
from utils.docker import wait_log_display
from utils.rand import get_rand_string
from utils.statistics import get_time

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


def enhance_joern_markup(container_name):
    try:
        docker_cli = docker.from_env()
        container = docker_cli.containers.get(container_name)
        container.start()

        wait_log_display(container, START_STRING)

        LOGGER.info("%s started. Running commands..." % container_name)
        for cmd in COMMANDS:
            try:
                start = get_time()
                container.exec_run("./bin/neo4j-shell -c \"%s\"" % cmd)
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

        LOGGER.info("%s fully converted." % container_name)
        container.stop()

    except APIError as ae:
        LOGGER.error(
            "An error occured while running %s: %s" %
            (container_name, ae.message)
        )


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
