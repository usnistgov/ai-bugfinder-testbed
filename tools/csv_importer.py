"""
"""
import csv
import pickle

import sys
from os.path import exists, isdir

from tools.settings import LOGGER

USAGE = "python ./tools/csv_importer.py ${CSV_AST_LIST}"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        LOGGER.error("Illegal number of arguments. Usage: %s." % USAGE)
        exit(1)

    if not exists(sys.argv[1]) or isdir(sys.argv[1]):
        LOGGER.error("Illegal argument #1. Argument should be a CSV file.")
        exit(2)

    # Init parameters
    ast_list = list()
    ast_list_append = ast_list.append
    features_list = list()
    features_list_append = features_list.append
    line_nb = -1

    with open(sys.argv[1], "r") as csv_file_handler:
        csv_reader = csv.reader(csv_file_handler)

        for line in csv_reader:
            line_nb += 1

            if line_nb == 0:
                continue

            ast_list_append(line[0])

    sorted_ast_list = sorted(ast_list)
    sorted_flow_list = sorted(["CONTROLS", "FLOWS_TO", "REACHES"])

    for source in sorted_ast_list:
        for flow in sorted_flow_list:
            for sink in sorted_ast_list:
                features_list_append("%s-%s-%s" % (source, flow, sink))

    with open("./features.bin", "wb") as features_file:
        pickle.dump(features_list, features_file)
