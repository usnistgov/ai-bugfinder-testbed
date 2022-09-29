""" Script to run feature extraction
"""

from os.path import dirname, join
import sys

sys.path.append(join(dirname(__file__), ".."))

import argparse

from bugfinder.base.dataset import CodeWeaknessClassificationDataset as Dataset
from bugfinder.processing.dataset.fix_rights import RightFixer
from bugfinder.features.extraction.bag_of_words.any_hop.all_flows import (
    FeatureExtractor as AnyHopAllFlowsExtractor,
)
from bugfinder.features.extraction.bag_of_words.any_hop.single_flow import (
    FeatureExtractor as AnyHopSingleFlowExtractor,
)
from bugfinder.features.extraction.bag_of_words.single_hop.raw import (
    FeatureExtractor as SingleHopRawExtractor,
)
from bugfinder.features.extraction.bag_of_words.hops_n_flows import (
    FeatureExtractor as HopsNFlowsExtractor,
)
from bugfinder.features.extraction.interproc import (
    FeatureExtractor as InterprocRawExtractor,
)
from bugfinder.utils.processing import is_operation_valid

if __name__ == "__main__":
    feature_extractors = {  # Available feature extractors
        "ahaf": AnyHopAllFlowsExtractor,
        "shr": SingleHopRawExtractor,
        "ahsf": AnyHopSingleFlowExtractor,
        "hnf": HopsNFlowsExtractor,
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
        help="feature extractor to use",
    )
    parser.add_argument(
        "--min",
        type=int,
        required=False,
        help="minimum number of hops",
    )
    parser.add_argument(
        "--max",
        type=int,
        required=False,
        help="maximum number of hops",
    )
    parser.add_argument(
        "--timeout", help="timeout for Neo4J queries", type=str, default="2h"
    )
    parser.add_argument(
        "--map-features",
        "-m",
        action="store_true",
        help="map features only (does not create csv file)",
    )

    args = parser.parse_args()

    # Instantiate dataset class and run joern processing
    dataset = Dataset(args.dataset_path)

    operation_class = feature_extractors[args.extractor]

    is_operation_valid(operation_class)

    dataset.queue_operation(RightFixer, {"command_args": "neo4j_v3.db 101 101"})

    operation_params = dict()

    if args.min:
        operation_params["min_hops"] = args.min

    if args.max:
        operation_params["max_hops"] = args.max

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
