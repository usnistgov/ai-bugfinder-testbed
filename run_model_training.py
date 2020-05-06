""" Script to run feature extraction
"""
import argparse

from bugfinder.dataset import CWEClassificationDataset as Dataset
from bugfinder.models.dnn_classifier import DNNClassifierTraining
from bugfinder.models.linear_classifier import LinearClassifierTraining
from bugfinder.utils.processing import is_operation_valid

if __name__ == "__main__":
    options = {  # Dictionary linking input arguments to processing classes
        "linear_classifier": LinearClassifierTraining,
        "deep_neural_network": DNNClassifierTraining,
    }

    # Setup the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_path", help="path to the dataset to clean")
    parser.add_argument(
        "--model",
        "-m",
        choices=options.keys(),
        required=True,
        help="path to the dataset to clean",
    )

    args = parser.parse_args()

    # Instantiate dataset class and run joern processing
    dataset = Dataset(args.dataset_path)

    operation_class = options[args.model]

    is_operation_valid(operation_class)

    dataset.queue_operation(operation_class)

    dataset.process()
