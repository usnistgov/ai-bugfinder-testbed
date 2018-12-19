""" Script cleaning literals from the code.
"""
from os import walk
from os.path import join, isdir, basename

import re
from shutil import move

import sys

from settings import LOGGER
from utils.statistics import get_time

USAGE = "./prepare_data.py ${DATA_DIR}"

replacements = {
    r'(.*)L\'([^\']*)\'(.*)': "\g<1>L('\g<2>')\g<3>",
    r'(.*)L"([^"]*)"(.*)': "\g<1>L(\"\g<2>\")\g<3>",
}

MAX_ITERATIONS = 500


def list_files_from(directory):
    file_list = []

    for path, subdir, files in walk(directory):
        for filename in files:
            file_list.append(join(path, filename))

    return file_list


def clean(file_list):
    current_file_list = file_list
    iteration = 0

    while len(current_file_list) != 0 and iteration < MAX_ITERATIONS:
        temp_file_list = []

        it_beg_time = get_time()
        for filename in current_file_list:
            outlines = []
            count_sub = 0

            # Try matching regexp on every line and correcting them if
            # necessary. Every time a new file is created
            with open(filename, 'r') as infile, \
                    open("%s.out" % filename, 'w+') as outfile:

                for line in infile:
                    for src, dest in replacements.items():
                        if re.match(src, line):
                            count_sub += 1
                            line = re.sub(src, dest, line)

                    outlines.append(line)

                outfile.writelines(outlines)

            # Replace the old file by the new one
            move("%s.out" % filename, filename)

            # If substitutions where made, log it and flag the file for an
            # additional pass.
            if count_sub > 0:
                temp_file_list.append(filename)
                LOGGER.info(
                    "%d substitution(s) performed on %s" %
                    (count_sub, basename(filename))
                )

        it_end_time = get_time()

        # Update env variables
        iteration += 1
        current_file_list = temp_file_list

        LOGGER.info(
            "Iteration %d performed in %dms." %
            (iteration, it_end_time - it_beg_time)
        )

    if iteration == MAX_ITERATIONS:
        LOGGER.warning("MAX_ITERATIONS was reached. Data could still be dirty!")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        LOGGER.error(
            "Illegal number of parameters. Usage: %s." % USAGE
        )
        exit(1)

    if not isdir(sys.argv[1]):
        LOGGER.error(
            "Argument ${DATA_DIR} should be a directory. Usage: %s." % USAGE
        )

    LOGGER.info("Starting cleaning data in %s..." % sys.argv[1])

    beg_time = get_time()
    datafile_list = list_files_from(sys.argv[1])
    clean(datafile_list)
    end_time = get_time()

    LOGGER.info("Cleaning terminated in %dms" % (end_time - beg_time))
