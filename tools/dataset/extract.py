"""
"""
from os import listdir, mkdir
from os.path import join, exists, isdir
from random import shuffle
from shutil import rmtree, copytree

import sys

from settings import ROOT_DIR, LOGGER
from utils.statistics import get_time

DATA_DIRNAME = join(ROOT_DIR, "data")
USAGE = "./python ./tools/dataset/extract.py ${ORIG_DIR} ${NB_SAMPLE} " \
        "${DEST_DIR}"

if __name__ == "__main__":
    if len(sys.argv) != 4:
        LOGGER.error("Illegal number of arguments. Usage: %s." % USAGE)
        exit(1)

    if not(exists(sys.argv[1])) or not isdir(sys.argv[1]):
        LOGGER.error("Input directory does not exist. Usage: %s." % USAGE)
        exit(1)

    if exists(sys.argv[3]):
        LOGGER.debug("Removing existing directory: %s..." % sys.argv[3])
        rmtree(sys.argv[3])

    # Setup parameters
    output_dirpath = sys.argv[3]
    output_dirpath_bad = join(output_dirpath, "bad")
    output_dirpath_good = join(output_dirpath, "good")
    input_dirpath_bad = join(sys.argv[1], "bad")
    input_dirpath_good = join(sys.argv[1], "good")
    dataset = listdir(input_dirpath_bad)
    sample_number = int(sys.argv[2])

    LOGGER.info("Shuffling and retrieving %d samples from %s" %
                (sample_number, sys.argv[1]))
    start = get_time()

    # Create sample list
    shuffle(dataset)
    sample_list = dataset[:sample_number]

    if exists(output_dirpath):
        rmtree(output_dirpath)

    mkdir(output_dirpath)
    mkdir(output_dirpath_bad)
    mkdir(output_dirpath_good)

    for sample in sample_list:
        orig_bad_sample_path = join(input_dirpath_bad, sample)
        dest_bad_sample_path = join(output_dirpath_bad, sample)
        orig_good_sample_path = join(input_dirpath_good, sample)
        dest_good_sample_path = join(output_dirpath_good, sample)

        copytree(orig_bad_sample_path, dest_bad_sample_path)
        copytree(orig_good_sample_path, dest_good_sample_path)

    end = get_time()
    LOGGER.info("New dataset extracted to %s in %dms" %
                (output_dirpath, end-start))
