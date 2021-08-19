""" Script to run feature selection
"""

import argparse

from bugfinder.dataset import CWEClassificationDataset as Dataset
from bugfinder.dataset.processing.dataset_ops import RightFixer
from bugfinder.features.reduction.pca import FeatureSelector as PCA
from bugfinder.features.reduction.variance_threshold import (
    FeatureSelector as VarianceThreshold,
)
from bugfinder.utils.processing import is_operation_valid

if __name__ == "__main__":
    feature_selectors = {  # Available feature selection and options
        "pca": {
            "class": PCA,
            "options": [
                {
                    "args": ["--dimension", "-d"],
                    "kwargs": {"type": int, "help": "output dimension"},
                }
            ],
        },
        "variance": {
            "class": VarianceThreshold,
            "options": [
                {
                    "args": ["--threshold", "-t"],
                    "kwargs": {"type": float, "help": "variance threshold"},
                }
            ],
        },
    }

    # Setup the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_path", help="path to the dataset to clean")
    parser.add_argument(
        "--selector",
        "-s",
        choices=feature_selectors.keys(),
        required=True,
        help="feature selector to chose",
    )
    parser.add_argument(
        "--dry-run",
        default=False,
        required=False,
        help="if specified, new features are not written in a CSV file",
        action="store_true",
    )

    selector_constraints = dict()
    for name, selector in feature_selectors.items():
        if "options" not in selector.keys():
            continue

        selector_constraints[name] = []

        for option in selector["options"]:
            option["kwargs"]["help"] += f" ({name} selector only)"

            argument = parser.add_argument(*option["args"], **option["kwargs"])
            selector_constraints[name].append(argument.dest)

    args = parser.parse_args()

    # Check required argument are all there and forbidden argument are not defined
    operation_args = {"dry_run": args.dry_run}
    required_args = selector_constraints[args.selector]
    forbidden_args = [
        constraint
        for selector, constraints in selector_constraints.items()
        for constraint in constraints
        if selector != args.selector
    ]

    for argument in forbidden_args:
        if getattr(args, argument):
            args_list = " ,".join([f"'{args}'" for args in required_args])
            parser.error(
                f"argument '{argument}' is not expected for selector {args.selector} "
                f"(choose from {args_list})"
            )

    for argument in required_args:
        argv = getattr(args, argument)
        if not argv:
            args_list = " ,".join([f"'{args}'" for args in required_args])
            parser.error(
                f"argument '{argument}' is missing for selector {args.selector} "
                f"(needs {args_list})"
            )

        operation_args[argument] = argv

    # Instantiate dataset class and run joern processing
    dataset = Dataset(args.dataset_path)

    operation_class = feature_selectors[args.selector]["class"]
    is_operation_valid(operation_class)
    dataset.queue_operation(operation_class, operation_args)

    dataset.process()
