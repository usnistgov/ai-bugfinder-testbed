from os.path import dirname, join
import sys

sys.path.append(join(dirname(__file__), ".."))

import argparse

from bugfinder.base.dataset import CodeWeaknessClassificationDataset as Dataset
from bugfinder.processing.dataset.fix_rights import RightFixer
from bugfinder.processing.joern.v031 import (
    JoernProcessing as Joern031Processing,
)
from bugfinder.processing.joern.v040 import (
    JoernProcessing as Joern040Processing,
)
from bugfinder.processing.neo4j.annot import Neo4JAnnotations
from bugfinder.processing.neo4j.converter import Neo4J2Converter, Neo4J3Converter
from bugfinder.processing.neo4j.importer import Neo4J3Importer
from bugfinder.utils.processing import is_processing_stack_valid

if __name__ == "__main__":
    options = {  # Dictionary linking input arguments to processing classes
        "0.3.1": [
            Joern031Processing,
            Neo4J2Converter,
            {"class": RightFixer, "args": {"command_args": "neo4j_v3.db 101 101"}},
            Neo4J3Converter,
            Neo4JAnnotations,
        ],
        "0.4.0": [
            Joern040Processing,
            Neo4J3Importer,
            {"class": RightFixer, "args": {"command_args": "neo4j_v3.db 101 101"}},
            Neo4JAnnotations,
        ],
    }

    # Setup the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_path", help="path to the dataset to clean")
    parser.add_argument(
        "--version",
        "-v",
        choices=options.keys(),
        required=True,
        help="path to the dataset to clean",
    )

    args = parser.parse_args()

    # Instantiate dataset class and run joern processing
    dataset = Dataset(args.dataset_path)

    if not is_processing_stack_valid(options[args.version]):
        raise TypeError("Invalid processing stack.")

    for operation in options[args.version]:
        if isinstance(operation, dict):
            dataset.queue_operation(operation["class"], operation["args"])
        else:  # operation is a DataProcessing class
            dataset.queue_operation(operation)

    dataset.process()
