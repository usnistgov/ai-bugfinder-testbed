import argparse
from inspect import isclass

from tools.dataset import CWEClassificationDataset as Dataset
from tools.dataset.processing import DatasetProcessing
from tools.dataset.processing.dataset_ops import RightFixer
from tools.joern.v031 import JoernDatasetProcessing as Joern031DatasetProcessing
from tools.joern.v040 import JoernDatasetProcessing as Joern040DatasetProcessing
from tools.neo4j.annot import Neo4JAnnotations
from tools.neo4j.converter import Neo4J2Converter, Neo4J3Converter
from tools.neo4j.importer import Neo4J3Importer

if __name__ == "__main__":
    def is_operation_valid(processing_operation):
        if isinstance(processing_operation, dict):
            assert "class" in processing_operation.keys() and \
                   "args" in processing_operation.keys()
            assert issubclass(processing_operation["class"], DatasetProcessing)
            assert isinstance(processing_operation["args"], dict)
        else:  # operation should be a sublass of dataset operation
            assert isclass(processing_operation)
            assert issubclass(processing_operation, DatasetProcessing)

    def is_processsing_stack_valid(operation_list):
        for processing_operation in operation_list:
            try:
                is_operation_valid(processing_operation)
            except AssertionError:
                return False

        return True

    options = {  # Dictionary linking input arguments to processing classes
        "0.3.1": [
            Joern031DatasetProcessing,
            Neo4J2Converter,
            {
                "class": RightFixer,
                "args": {"command_args": "neo4j_v3.db 101 101"}
            },
            Neo4J3Converter,
            Neo4JAnnotations
        ],
        "0.4.0": [
            Joern040DatasetProcessing,
            Neo4J3Importer,
            {
                "class": RightFixer,
                "args": {"command_args": "neo4j_v3.db 101 101"}
            },
            Neo4JAnnotations
        ]
    }

    # Setup the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_path", help="path to the dataset to clean")
    parser.add_argument("--version", "-v", choices=options.keys(), required=True,
                        help="path to the dataset to clean")

    args = parser.parse_args()

    # Instantiate dataset class and run joern processing
    dataset = Dataset(args.dataset_path)

    if not is_processsing_stack_valid(options[args.version]):
        raise TypeError("Invalid processing stack.")

    for operation in options[args.version]:
        if isinstance(operation, dict):
            dataset.queue_operation(operation["class"], operation["args"])
        else:  # operation is a DataProcessing class
            dataset.queue_operation(operation)

    dataset.process()
