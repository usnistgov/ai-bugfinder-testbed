""" Script to markup nodes with an AST structure
"""

from os.path import dirname, join
import sys

sys.path.append(join(dirname(__file__), ".."))

import argparse

from bugfinder.ast.v01 import Neo4JASTMarkup as Neo4JASTMarkupV01
from bugfinder.ast.v02 import Neo4JASTMarkup as Neo4JASTMarkupV02
from bugfinder.ast.v03 import Neo4JASTMarkup as Neo4JASTMarkupV03
from bugfinder.dataset import CodeWeaknessClassificationDataset as Dataset
from bugfinder.dataset.processing.dataset_ops import RightFixer
from bugfinder.utils.processing import is_processing_stack_valid

if __name__ == "__main__":
    options = [  # List of processing classes
        [
            {"class": RightFixer, "args": {"command_args": "neo4j_v3.db 101 101"}},
            Neo4JASTMarkupV01,
        ],
        [
            {"class": RightFixer, "args": {"command_args": "neo4j_v3.db 101 101"}},
            Neo4JASTMarkupV02,
        ],
        [
            {"class": RightFixer, "args": {"command_args": "neo4j_v3.db 101 101"}},
            Neo4JASTMarkupV03,
        ],
    ]

    # Setup the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_path", help="path to the dataset to clean")
    parser.add_argument(
        "--version",
        "-v",
        choices=range(1, len(options) + 1),
        type=int,
        required=True,
        help="path to the dataset to clean",
    )

    args = parser.parse_args()

    # Instantiate dataset class and run AST markup processing
    dataset = Dataset(args.dataset_path)

    if not is_processing_stack_valid(options[args.version - 1]):
        raise TypeError("Invalid processing stack.")

    for operation in options[args.version - 1]:
        if isinstance(operation, dict):
            dataset.queue_operation(operation["class"], operation["args"])
        else:  # operation is a DataProcessing class
            dataset.queue_operation(operation)

    dataset.process()
