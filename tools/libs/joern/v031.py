""" Execute code analysis with Joern v0.3.1
"""
from os.path import join

from libs.joern.common import run_joern_lite
from libs.neo4j.v23 import start_container as run_neo4j_v2
from libs.neo4j.ai import start_container as run_neo4j_v3, enhance_markup
from settings import LOGGER
from utils.dirs import copy_dir


def main(code_path):
    LOGGER.info("Starting Joern 0.3.1...")
    run_joern_lite("0.3.1", code_path)

    LOGGER.info("Joern database generated. Preparing update to Neo4j 2.3...")
    src = join(code_path, "joern.db")
    dest = join(code_path, "neo4j_v2.db")
    copy_dir(src, dest)

    LOGGER.info("Database ready. Updating to Neo4j 2.3...")
    run_neo4j_v2(dest)

    LOGGER.info(
        "Database updated to Neo4J 2.3. Preparing update to Neo4j 3.5..."
    )
    src = dest
    dest = join(code_path, "neo4j_v3.db")
    copy_dir(src, dest)

    LOGGER.info("Database ready. Updating to Neo4j 3.5...")
    run_neo4j_v3(dest, stop_after_execution=True)
    enhance_markup(dest)
