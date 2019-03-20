"""
"""
from os.path import join, exists, isdir
from shutil import rmtree, copytree

import sys

from settings import ROOT_DIR, LOGGER
from utils.statistics import get_time

DATA_DIRNAME = join(ROOT_DIR, "data")
USAGE = "python ./tools/dataset/duplicate.py ${DATASET1} ${DATASET2}"

if __name__ == "__main__":
    if len(sys.argv) != 3:
        LOGGER.error("Illegal number of arguments. Usage: %s." % USAGE)
        exit(1)

    if not(exists(sys.argv[1])) or not isdir(sys.argv[1]):
        LOGGER.error("Input directory does not exist. Usage: %s." % USAGE)
        exit(1)

    LOGGER.info("Duplicating %s to %s" % (sys.argv[1], sys.argv[2]))
    start = get_time()

    if exists(sys.argv[2]):
        rmtree(sys.argv[2])

    copytree(sys.argv[1], sys.argv[2])
    end = get_time()

    LOGGER.info("Copy terminated in %dms" % (end-start))

