""" Script to limit to c test
"""
import sys
import os
from os import remove
from os.path import join, splitext
from shutil import rmtree

from settings import LOGGER, ROOT_DIR
from utils.statistics import get_time

USAGE = "python ./tools/filter_cpp_tc.py ${DATA_DIR}"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        LOGGER.error("Illegal number of arguments. Usage: %s." % USAGE)
        exit(1)

    data_dir = join(ROOT_DIR, sys.argv[1])

    LOGGER.info("Pass 1/2: Removal of CPP files...")
    rm_count = 0
    start = get_time()

    for dirname, sudirs, filelist in os.walk(data_dir):
        for filename in filelist:
            (filetype, fileext) = splitext(filename)

            if fileext == ".cpp":
                rm_count += 1
                LOGGER.info("Removing %s..." % join(dirname, filename))
                remove(join(dirname, filename))

    end = get_time()
    LOGGER.info("Removed %d files in %dms." % (rm_count, end - start))
    LOGGER.info("Pass 2/2: Remove of empty test cases")
    rm_count = 0
    start = get_time()

    for dirname, sudirs, filelist in os.walk(data_dir):
        filecount = 0

        for filename in filelist:
            (filetype, fileext) = splitext(filename)

            if fileext != ".h":
                filecount += 1
                break

        if filecount == 0 and len(sudirs) == 0:
            rm_count += 1
            LOGGER.info("Removing %s..." % dirname)
            rmtree(dirname)

    end = get_time()
    LOGGER.info("Removed %d test cases in %dms." % (rm_count, end-start))
