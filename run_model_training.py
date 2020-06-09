""" Script to run feature extraction
"""
import argparse
import logging
import os

from bugfinder.dataset import CWEClassificationDataset as Dataset
from bugfinder.models.dnn_classifier import DNNClassifierTraining
from bugfinder.models.linear_classifier import LinearClassifierTraining
from bugfinder.settings import LOGGER
from bugfinder.utils.processing import is_operation_valid

if __name__ == "__main__":
    # Deactivate tensorflow logging
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "0"  # {'0', '1', '2', '3'}
    logging.getLogger("tensorflow").setLevel(logging.FATAL)
    LOGGER.propagate = False

    options = {  # Dictionary linking input arguments to processing classes
        "linear_classifier": LinearClassifierTraining,
        "deep_neural_network": DNNClassifierTraining,
    }

    # Setup the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_path", help="path to the dataset to clean")
    parser.add_argument(
        "--model", "-m", choices=options.keys(), required=True, help="model to use",
    )
    parser.add_argument(
        "--name", "-n", required=True, help="name to the saved model",
    )

    args = parser.parse_args()

    # Instantiate dataset class and run model training
    dataset = Dataset(args.dataset_path)

    operation = {
        "class": options[args.model],
        "args": {"name": args.name},
    }

    is_operation_valid(operation)

    dataset.queue_operation(operation["class"], operation["args"])

    dataset.process()
