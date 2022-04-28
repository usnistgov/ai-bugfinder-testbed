from os.path import dirname, join
import sys

sys.path.append(join(dirname(__file__), ".."))

import argparse

from bugfinder.base.dataset import CodeWeaknessClassificationDataset as Dataset

from bugfinder.features.extraction.word2vec.embeddings import Word2VecEmbeddings
from bugfinder.features.extraction.node2vec.embeddings import Node2VecEmbeddings

from bugfinder.utils.processing import is_operation_valid

if __name__ == "__main__":
    options = {"word2vec": Word2VecEmbeddings, "node2vec": Node2VecEmbeddings}

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--name",
        "-n",
        required=True,
        help="Which type of embeddings to generate (word2vec or node2vec)",
    )

    parser.add_argument(
        "dataset_path",
        help="Path to the dataset containting the files to generate the embeddings",
    )

    parser.add_argument(
        "--model",
        "-m",
        required=True,
        help="Path to the word2vec model to be used to generated the embeddings",
    )
    parser.add_argument(
        "--emb_length",
        "-el",
        required=False,
        default=300,
        type=int,
        help="Size of the embedding vector to be created",
    )
    parser.add_argument(
        "--vec_length",
        "-vl",
        required=False,
        default=50,
        type=int,
        help="Size of the embedding vector to be created",
    )

    args = parser.parse_args()
    kwargs = dict()

    dataset = Dataset(args.dataset_path)

    op_args = {
        "name": args.name,
        "model": args.model,
        "emb_length": args.emb_length,
        "vec_length": args.vec_length,
    }

    op_args.update(kwargs)

    operation = {
        "class": options[args.name],
        "args": op_args,
    }

    is_operation_valid(operation)

    dataset.queue_operation(operation["class"], operation["args"])

    dataset.process()
