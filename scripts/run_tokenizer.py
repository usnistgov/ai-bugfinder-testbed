from os.path import dirname, join

import sys

sys.path.append(join(dirname(__file__), ".."))

import argparse

from bugfinder.base.dataset import CodeWeaknessClassificationDataset as Dataset

from bugfinder.processing.tokenizers.replace_functions import ReplaceFunctions
from bugfinder.processing.tokenizers.replace_variables import ReplaceVariables
from bugfinder.processing.tokenizers.tokenize_code import TokenizeCode


if __name__ == "__main__":
    options = {
        "replace_funcs": ReplaceFunctions,
        "replace_vars": ReplaceVariables,
        "tokenize": TokenizeCode,
    }

    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_path", help="path to the dataset to clean")

    for option in options.keys():
        parser.add_argument("--%s" % option.replace("_", "-"), action="store_true")

    args = vars(parser.parse_args())

    dataset = Dataset(args["dataset_path"])

    for option_name, option_class in options.items():
        if args[option_name]:
            dataset.queue_operation(option_class)

    dataset.process()
