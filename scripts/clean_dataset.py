""" Script to clean a dataset from problematic code samples.
"""
from os.path import dirname, join

import sys

sys.path.append(join(dirname(__file__), ".."))

import argparse

from bugfinder.base.dataset import CodeWeaknessClassificationDataset as Dataset

from bugfinder.processing.cleaning.remove_cpp_files import RemoveCppFiles
from bugfinder.processing.cleaning.remove_interproc_files import RemoveInterprocFiles
from bugfinder.processing.cleaning.remove_main_function import RemoveMainFunction
from bugfinder.processing.cleaning.replace_litterals import ReplaceLitterals
from bugfinder.processing.cleaning.remove_comments import RemoveComments


if __name__ == "__main__":
    options = {  # Dictionary linking input arguments to processing classes
        "no_cpp": RemoveCppFiles,
        "no_interprocedural": RemoveInterprocFiles,
        "no_litterals": ReplaceLitterals,
        "no_main": RemoveMainFunction,
        "no_comments": RemoveComments,
    }

    # Setup the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_path", help="path to the dataset to clean")

    for option in options.keys():
        parser.add_argument("--%s" % option.replace("_", "-"), action="store_true")

    # Convert arguments into a dictionary
    args = vars(parser.parse_args())

    # Instantiate dataset class
    dataset = Dataset(args["dataset_path"])

    for option_name, option_class in options.items():
        if args[option_name]:
            dataset.queue_operation(option_class)

    dataset.process()
