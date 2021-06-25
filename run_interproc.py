""" Script to markup nodes with an AST structure
"""
import argparse

from bugfinder.interproc import InterprocMerger
from bugfinder.dataset.processing.dataset_ops import RightFixer
from bugfinder.utils.processing import is_processing_stack_valid
from bugfinder.dataset import CWEClassificationDataset as Dataset

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_path", help="path to the dataset", type=str)
    parser.add_argument(
        "--log_failed",
        help="path to a file to log failed queries",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--run_failed",
        help="path to the log file of failed queries",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--timeout", help="timeout for Neo4J queries", type=str, default="2h"
    )
    args = parser.parse_args()

    dataset = Dataset(args.dataset_path)
    dataset.queue_operation(RightFixer, {"command_args": "neo4j_v3.db 101 101"})
    dataset.queue_operation(
        InterprocMerger,
        {
            "command_args": {
                "log_input": args.run_failed,
                "log_output": args.log_failed,
            },
            "container_config": {
                "timeout": args.timeout,
            },
        },
    )
    dataset.process()
