import argparse

from bugfinder.dataset import CWEClassificationDataset as Dataset
from bugfinder.dataset.processing.word2vec_ops import (
    RemoveComments,
    ReplaceFunctions,
    ReplaceVariables
)
from bugfinder.dataset.processing.token_ops import (
    TokenizeText
)


if __name__ == "__main__":
    options = { 
        "no_comments": RemoveComments,
        "replace_funcs": ReplaceFunctions,
        "replace_vars": ReplaceVariables,
        "tokenize": TokenizeText
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
