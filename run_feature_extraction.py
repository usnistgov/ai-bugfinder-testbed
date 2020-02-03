""" Script to run feature extraction
"""
import argparse

from tools.dataset import CWEClassificationDataset as Dataset, CWEClassificationDataset
from tools.dataset.processing.dataset_ops import RightFixer
from tools.features.any_hop.all_flows import FeatureExtractor as AnyHopAllFlowsExtractor
from tools.features.any_hop.single_flow import FeatureExtractor as AnyHopSingleFlowExtractor
from tools.features.pca import FeatureExtractor as PCA
from tools.features.single_hop.raw import FeatureExtractor as SingleHopRawExtractor
from tools.utils.processing import is_operation_valid

if __name__ == "__main__":
    options = {  # Dictionary linking input arguments to processing classes
        "ahaf": AnyHopAllFlowsExtractor,
        "shr": SingleHopRawExtractor,
        "ahsf": AnyHopSingleFlowExtractor
    }

    # Setup the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_path", help="path to the dataset to clean")
    parser.add_argument("--extractor", "-e", choices=options.keys(), required=True,
                        help="path to the dataset to clean")

    option_group = parser.add_mutually_exclusive_group()
    option_group.add_argument("--map-features", "-m", action="store_true",
                              help="path to the dataset to clean")
    option_group.add_argument("--pca", "-p", metavar="pca", default=0,
                              type=int, help="number of sample to extract")

    args = parser.parse_args()

    # Instantiate dataset class and run joern processing
    dataset = Dataset(args.dataset_path)

    operation_class = options[args.extractor]

    is_operation_valid(operation_class)

    dataset.queue_operation(RightFixer, {"command_args": "neo4j_v3.db 101 101"})

    if args.map_features:
        dataset.queue_operation(operation_class, {"need_map_features": True})
    else:
        dataset.queue_operation(operation_class)

    if args.pca > 0:
        dataset.queue_operation(PCA, {"final_dimension": args.pca})

    dataset.process()
