"""
"""
import sys
from os import listdir, mkdir
from os.path import exists, isdir, join
from shutil import rmtree, copytree

from settings import LOGGER, ROOT_DIR

USAGE = "python ./tools/dataset/inverse.py ${DATASET1} ${DATASET2} ${DATASET3}"

if __name__ == "__main__":
    if len(sys.argv) != 4:
        LOGGER.error("Illegal number of arguments. Usage: %s." % USAGE)
        exit(1)

    base_dir = join(ROOT_DIR, sys.argv[1])
    if not(exists(base_dir)) or not isdir(base_dir):
        LOGGER.error("Base directory does not exist. Usage: %s." % USAGE)
        exit(1)

    derived_dir = join(ROOT_DIR, sys.argv[2])
    if not(exists(derived_dir)) or not isdir(derived_dir):
        LOGGER.error("Derived directory does not exist. Usage: %s." % USAGE)
        exit(1)

    derived_sample_list = listdir(join(derived_dir, "bad"))
    inverse_sample_list = [
        sample for sample in listdir(join(base_dir, "bad"))
        if sample not in derived_sample_list
    ]

    output_dirpath = join(ROOT_DIR, sys.argv[3])
    output_dirpath_bad = join(output_dirpath, "bad")
    output_dirpath_good = join(output_dirpath, "good")

    input_dirpath_bad = join(base_dir, "bad")
    input_dirpath_good = join(base_dir, "good")

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


