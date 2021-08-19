""" Script to run feature selection
"""
from copy import deepcopy

import argparse
import re

from bugfinder.dataset import CWEClassificationDataset as Dataset
from bugfinder.features.reduction.pca import FeatureSelector as PCA
from bugfinder.features.reduction.select_from_model import (
    FeatureSelector as SelectFromModel,
)
from bugfinder.features.reduction.univariate_select import (
    FeatureSelector as UnivariateSelect,
)
from bugfinder.features.reduction.variance_threshold import (
    FeatureSelector as VarianceThreshold,
)
from bugfinder.features.reduction.recursive_feature_elimination import (
    FeatureSelector as RecursiveFeatureElimination,
)
from bugfinder.features.reduction.sequential_feature_selector import (
    FeatureSelector as SequentialFeatureSelector,
)
from bugfinder.utils.feature_selection import selection_estimators
from bugfinder.utils.processing import is_operation_valid

if __name__ == "__main__":
    generic_options = {
        "dimension": {
            "args": ["--dimension", "-dm"],
            "kwargs": {"type": int, "help": "output dimension"},
        },
        "model": {
            "args": ["--model", "-ml"],
            "kwargs": {
                "choices": selection_estimators().keys(),
                "help": "model to use for feature selection",
            },
        },
        "features": {
            "args": ["--features", "-ft"],
            "kwargs": {"type": int, "help": "number of features to keep"},
        },
    }

    feature_selectors = {  # Available feature selection and options
        "pca": {
            "class": PCA,
            "options": [generic_options["dimension"]],
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
        "univariate": {
            "class": UnivariateSelect,
            "options": [
                {
                    "args": ["--function", "-fn"],
                    "kwargs": {
                        "choices": [
                            "chi2",
                            "f_classif",
                            "mutual_info_classif",
                        ],
                        "help": "score function",
                    },
                },
                {
                    "args": ["--mode", "-md"],
                    "kwargs": {
                        "choices": ["k_best", "percentile", "fpr", "fdr", "fwe"],
                        "help": "selection mode",
                    },
                },
                {
                    "args": ["--param", "-p"],
                    "kwargs": {"type": float, "help": "selection mode parameter"},
                },
            ],
        },
        "from_model": {
            "class": SelectFromModel,
            "options": [generic_options["model"]],
        },
        "rfe": {
            "class": RecursiveFeatureElimination,
            "options": [
                generic_options["model"],
                generic_options["features"],
                {
                    "args": ["--cross-validation", "-cv"],
                    "kwargs": {"type": bool, "help": "use cross-validation"},
                },
            ],
        },
        "sfs": {
            "class": SequentialFeatureSelector,
            "options": [
                generic_options["model"],
                generic_options["features"],
                {
                    "args": ["--direction", "-dr"],
                    "kwargs": {
                        "choices": ["forward", "backward"],
                        "help": "direction of the feature selection",
                    },
                },
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
        help="feature selector to apply",
    )
    parser.add_argument(
        "--dry-run",
        default=False,
        required=False,
        help="if specified, new features are not written in a CSV file",
        action="store_true",
    )

    default_constraints = ["dataset_path", "selector", "dry_run"]

    selector_constraints = dict()
    options_map = dict()

    # Define args necessary for each selector and establish the list of options to add
    # to the parser.
    for name, selector in feature_selectors.items():
        if "options" not in selector.keys():
            continue

        selector_constraints[name] = deepcopy(default_constraints)

        for option in selector["options"]:
            option_name = option["args"][0].replace("--", "")
            option_name = option_name.replace("-", "_")

            if option_name in options_map.keys():
                options_map[option_name]["kwargs"]["help"] = re.sub(
                    r"^([^\(]+\(for )([^ ]+)( selector\))",
                    rf"\1\2,{name}\3",
                    option["kwargs"]["help"],
                )
            else:
                option["kwargs"]["help"] += f" (for {name} selector)"
                options_map[option_name] = option

            selector_constraints[name].append(option_name)

    # Add the options to the parser
    for option in options_map.values():
        parser.add_argument(*option["args"], **option["kwargs"])

    args = parser.parse_args()

    # Check required arguments are all present and forbidden arguments are not defined
    operation_args = {"dry_run": args.dry_run}

    provided_args = set([key for key, value in vars(args).items() if value is not None])
    required_args = set(selector_constraints[args.selector])
    arg_list = [
        args
        for args in selector_constraints[args.selector]
        if args not in default_constraints
    ]
    arg_helper = ",".join([f"'{args}'" for args in arg_list])

    for argument in arg_list:
        operation_args[argument] = getattr(args, argument)

    forbidden_args = provided_args.difference(required_args)
    missing_args = required_args.difference(provided_args)

    if len(forbidden_args) > 0:  # If forbidden argument were found.
        parser.error(
            f"argument '{forbidden_args.pop()}' is not expected for selector "
            f"'{args.selector}' (choose from {arg_helper})"
        )

    if len(missing_args) > 0:  # If missing arguments were found.
        parser.error(
            f"argument '{missing_args.pop()}' is missing for selector '{args.selector}' "
            f"(choose from {arg_helper})"
        )

    # Instantiate dataset class and run joern processing
    dataset = Dataset(args.dataset_path)

    operation_class = feature_selectors[args.selector]["class"]
    is_operation_valid(operation_class)
    dataset.queue_operation(operation_class, operation_args)

    dataset.process()
