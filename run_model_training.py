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
        "--name", "-n", required=True, help="name of the saved model",
    )
    parser.add_argument(
        "--batch-size",
        "-b",
        required=False,
        default=100,
        type=int,
        help="batch size for processing data (default=100)",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        required=False,
        help="max number of items to train with",
    )
    parser.add_argument(
        "--epochs", "-e", type=int, default=1, required=False, help="number of epochs",
    )
    parser.add_argument(
        "--keep-best-model",
        "-k",
        required=False,
        default=False,
        help="keep the best performing model",
        action="store_true",
    )
    parser.add_argument(
        "--reset",
        "-r",
        default=False,
        required=False,
        help="overwrite an existing model",
        action="store_true",
    )
    parser.add_argument(
        "--architecture",
        "-a",
        default="10,10,10",
        required=False,
        help="architecture of the DNN",
    )

    args = parser.parse_args()
    kwargs = dict()

    if args.model != "deep_neural_network":
        LOGGER.warning("Architecture param discarded (%s)" % args.model)
    else:
        kwargs["architecture"] = args.architecture.split(",")

    # Instantiate dataset class and run model training
    dataset = Dataset(args.dataset_path)

    op_args = {
        "name": args.name,
        "batch_size": args.batch_size,
        "max_items": args.limit,
        "epochs": args.epochs,
        "keep_best_model": args.keep_best_model,
        "reset": args.reset,
    }
    op_args.update(kwargs)

    operation = {
        "class": options[args.model],
        "args": op_args,
    }

    is_operation_valid(operation)

    dataset.queue_operation(operation["class"], operation["args"])

    dataset.process()
