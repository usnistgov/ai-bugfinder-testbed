""" Script to run feature extraction
"""

from os.path import dirname, join
import sys

sys.path.append(join(dirname(__file__), ".."))

import argparse

from bugfinder.dataset import CWEClassificationDataset as Dataset
from bugfinder.dataset.processing.dataset_ops import RightFixer
from bugfinder.features.extraction.any_hop.all_flows import (
    FeatureExtractor as AnyHopAllFlowsExtractor,
)
from bugfinder.features.extraction.any_hop.single_flow import (
    FeatureExtractor as AnyHopSingleFlowExtractor,
)
from bugfinder.features.extraction.single_hop.raw import (
    FeatureExtractor as SingleHopRawExtractor,
)
from bugfinder.features.interproc.raw import FeatureExtractor as InterprocRawExtractor
from bugfinder.utils.processing import is_operation_valid

if __name__ == "__main__":
    feature_extractors = {  # Available feature extractors
        "ahaf": AnyHopAllFlowsExtractor,
        "shr": SingleHopRawExtractor,
        "ahsf": AnyHopSingleFlowExtractor,
        "iprc": InterprocRawExtractor,
    }

    # Setup the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_path", help="path to the dataset to clean")
    parser.add_argument(
        "--extractor",
        "-e",
        choices=feature_extractors.keys(),
        required=True,
        help="path to the dataset to clean",
    )
    parser.add_argument(
        "--timeout", help="timeout for Neo4J queries", type=str, default="2h"
    )
    parser.add_argument(
        "--map-features", "-m", action="store_true", help="path to the dataset to clean"
    )

    args = parser.parse_args()

    # Instantiate dataset class and run joern processing
    dataset = Dataset(args.dataset_path)

    operation_class = feature_extractors[args.extractor]

    is_operation_valid(operation_class)

    dataset.queue_operation(RightFixer, {"command_args": "neo4j_v3.db 101 101"})

    operation_params = dict()

    if args.map_features:
        operation_params["need_map_features"] = True

    # FIXME modify docker processing to have extra container configuration without
    #   raising error.
    if args.timeout and args.extractor == "iprc":
        operation_params["container_config"] = {"timeout": args.timeout}

    if len(operation_params.keys()) > 0:
        dataset.queue_operation(operation_class, operation_params)
    else:
        dataset.queue_operation(operation_class)

    dataset.process()
