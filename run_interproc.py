""" Script to markup nodes with an AST structure
"""
import argparse

from bugfinder.interproc import InterprocMerger
from bugfinder.dataset import CWEClassificationDataset as Dataset
from bugfinder.dataset.processing.dataset_ops import RightFixer
from bugfinder.utils.processing import is_processing_stack_valid

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_path", help="path to the dataset to clean")
    args = parser.parse_args()

    dataset = Dataset(args.dataset_path)
    dataset.queue_operation(RightFixer, {"command_args": "neo4j_v3.db 101 101"})
    dataset.queue_operation(InterprocMerger)
    dataset.process()
