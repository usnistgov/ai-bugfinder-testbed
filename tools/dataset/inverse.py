"""
"""
import sys
from os import listdir, mkdir
from os.path import exists, isdir, join
from shutil import rmtree, copytree

from settings import LOGGER

USAGE = "python ./tools/dataset/inverse.py ${DATASET1} ${DATASET2} ${DATASET3}"

if __name__ == "__main__":
    if len(sys.argv) != 4:
        LOGGER.error("Illegal number of arguments. Usage: %s." % USAGE)
        exit(1)

    if not(exists(sys.argv[1])) or not isdir(sys.argv[1]):
        LOGGER.error("Base directory does not exist. Usage: %s." % USAGE)
        exit(1)

    if not(exists(sys.argv[2])) or not isdir(sys.argv[2]):
        LOGGER.error("Derived directory does not exist. Usage: %s." % USAGE)
        exit(1)

    derived_sample_list = listdir(join(sys.argv[2], "bad"))
    inverse_sample_list = [
        sample for sample in listdir(join(sys.argv[1], "bad"))
        if sample not in derived_sample_list
    ]

    output_dirpath = sys.argv[3]
    output_dirpath_bad = join(output_dirpath, "bad")
    output_dirpath_good = join(output_dirpath, "good")

    input_dirpath_bad = join(sys.argv[1], "bad")
    input_dirpath_good = join(sys.argv[1], "good")

    if exists(output_dirpath):
        rmtree(output_dirpath)

    mkdir(output_dirpath)
    mkdir(output_dirpath_bad)
    mkdir(output_dirpath_good)

    for sample in inverse_sample_list:
        orig_bad_sample_path = join(input_dirpath_bad, sample)
        dest_bad_sample_path = join(output_dirpath_bad, sample)
        orig_good_sample_path = join(input_dirpath_good, sample)
        dest_good_sample_path = join(output_dirpath_good, sample)

        copytree(orig_bad_sample_path, dest_bad_sample_path)
        copytree(orig_good_sample_path, dest_good_sample_path)


