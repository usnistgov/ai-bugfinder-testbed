""" Script running Joern and providing a Neo4j v3 DB
"""
from os.path import join
import sys

from settings import ROOT_DIR, LOGGER
from libs.joern.v031 import main as run_joern_v031
from libs.joern.v040 import main as run_joern_v040

USAGE = "python ./tools/run_joern.py ${DATA_DIR} ${VERSION}"

joern_versions = {
    "0.3.1": run_joern_v031,
    "0.4.0": run_joern_v040
}

if __name__ == "__main__":
    if len(sys.argv) != 3:
        LOGGER.error("Illegal number of arguments. Usage: %s." % USAGE)
        exit(1)

    code_path = join(ROOT_DIR, sys.argv[1])

    if sys.argv[2] not in joern_versions.keys():
        LOGGER.error(
            "Illegal argument: 'version' not in %s" % str(joern_versions.keys())
        )
        exit(1)

    joern_versions[sys.argv[2]](code_path)
