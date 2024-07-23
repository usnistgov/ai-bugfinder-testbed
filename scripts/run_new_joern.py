""" 
Script to run Joern v2.0.107. The input arguments are used to parse
and export the Code Property Graph using Joern's scripts
"""
from os.path import dirname, join
import sys

sys.path.append(join(dirname(__file__), ".."))

import argparse

from bugfinder.processing.joern.v2010 import JoernProcessing
from bugfinder.base.dataset import CodeWeaknessClassificationDataset as Dataset

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_path", help="path to the dataset", type=str)
    parser.add_argument(
        "--language",
        help="Language of the files to be processed",
        type=str,
        default='c',
    )
    parser.add_argument(
        "--repr",
        help="Which representation the Code Property Graph will be extracted."
        "Options here are the same as the ones on joern-export: "
        "all|ast|cdg|cfg|cpg|cpg14|ddg|pdg",
        type=str,
        default='cpg14',
    )
    parser.add_argument(
        "--format",
        help="Which format the graph will be exported."
        "Options here are the same as the ones on joern-export:"
        "dot|graphml|graphson|neo4jcsv",
        type=str,
        default='dot',
    )

    args = parser.parse_args()

    dataset = Dataset(args.dataset_path)

    dataset.queue_operation(
        JoernProcessing,
        {
            "language": args.language, 
            "repr_type": args.repr, 
            "output_format": args.format
        },
    )
    
    dataset.process()
