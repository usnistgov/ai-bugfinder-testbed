"""

"""
import sys
from os.path import join, dirname

from py2neo import Graph

from features.rel_count_multi_v31 import extract_features as \
    extract_features_v31
from features.rel_count_multi_v40 import extract_features as \
    extract_features_v40
from features.rel_count_simple import extract_features as \
    extract_features_v41
from libs.neo4j.ai import start_container as run_neo4j_v3
from settings import ROOT_DIR, LOGGER
from utils.containers import stop_container_by_name

USAGE = "./extract_features.py ${DATA_DIR} ${DATA_VERSION}"

COMMANDS = {
    "0.3.1": extract_features_v31,
    "0.4.0": extract_features_v40,
    "0.4.1": extract_features_v41
}

if __name__ == "__main__":
    if len(sys.argv) != 3:
        LOGGER.error("Illegal number of arguments. Usage: %s." % USAGE)
        exit(1)

    db_path = join(ROOT_DIR, sys.argv[1])

    neo4j_container_obj, neo4j_container_name = run_neo4j_v3(db_path, stop_after_execution=False)

    # Neo4j database pre-loaded with Joern
    neo4j_db = Graph(
        scheme="http",
        host="0.0.0.0",
        port="7474"
    )

    COMMANDS[sys.argv[2]](neo4j_db, dirname(db_path))

    stop_container_by_name(neo4j_container_name)

