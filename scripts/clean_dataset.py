""" Script to clean a dataset from problematic code samples.
"""
from os.path import dirname, join
import sys

sys.path.append(join(dirname(__file__), ".."))

import argparse

from bugfinder.dataset import CWEClassificationDataset as Dataset
from bugfinder.dataset.processing.content_ops import (
    RemoveMainFunction,
    ReplaceLitterals,
)
from bugfinder.dataset.processing.file_ops import (
    RemoveCppFiles,
    RemoveInterproceduralTestCases,
)


if __name__ == "__main__":
    options = {  # Dictionary linking input arguments to processing classes
        "no_cpp": RemoveCppFiles,
        "no_interprocedural": RemoveInterproceduralTestCases,
        "no_litterals": ReplaceLitterals,
        "no_main": RemoveMainFunction,
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
