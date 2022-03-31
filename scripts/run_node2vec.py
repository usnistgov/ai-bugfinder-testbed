""" Script to run feature extraction
"""

from os.path import dirname, join
import sys

sys.path.append(join(dirname(__file__), ".."))

import argparse
import logging
import os

from bugfinder.dataset import CodeWeaknessClassificationDataset as Dataset

from bugfinder.models.node2vec import Node2VecTraining

from bugfinder.settings import LOGGER
from bugfinder.utils.processing import is_operation_valid

if __name__ == "__main__":
    options = {  # Dictionary linking input arguments to processing classes
        "node2vec": Node2VecTraining,
    }

    # Setup the argument parser
    parser = argparse.ArgumentParser()

    parser.add_argument("dataset_path", help="path to the dataset to clean")

    parser.add_argument(
        "--model",
        "-m",
        choices=options.keys(),
        required=True,
        help="model to use",
    )
    parser.add_argument(
        "--name",
        "-n",
        required=True,
        help="path where the trained model will be saved",
    )
    parser.add_argument(
        "--vec_length",
        "-vl",
        required=False,
        default=64,
        type=int,
        help="dimensions of the embedding vector to be created",
    )
    parser.add_argument(
        "--num_walks",
        required=False,
        default=50,
        type=int,
        help="number of walks per node",
    )
    parser.add_argument(
        "--walk_length",
        "-wl",
        required=False,
        default=100,
        type=int,
        help="number of nodes visited in each walk",
    )
    parser.add_argument(
        "--p_prob",
        "-p",
        required=False,
        default=1,
        type=int,
        help="return hyperparameter for the random walk",
    )
    parser.add_argument(
        "--q_prob",
        "-q",
        required=False,
        default=1,
        type=int,
        help="inout hyperparameter for the random walk",
    )
    parser.add_argument(
        "--seed",
        "-s",
        required=False,
        default=32,
        type=int,
        help="seed for the training for reproducibility purposes",
    )

    args = parser.parse_args()
    kwargs = dict()

    # Instantiate dataset class for model training
    dataset = Dataset(args.dataset_path)

    op_args = {
        "name": args.name,
        "vec_length": args.vec_length,
        "num_walks": args.num_walks,
        "walk_length": args.walk_length,
        "p": args.p_prob,
        "q": args.q_prob,
        "seed": args.seed,
    }
    op_args.update(kwargs)

    operation = {
        "class": options[args.model],
        "args": op_args,
    }

    is_operation_valid(operation)

    dataset.queue_operation(operation["class"], operation["args"])

    dataset.process()
