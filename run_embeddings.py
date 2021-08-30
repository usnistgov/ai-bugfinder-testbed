import argparse
import logging
import os

from bugfinder.dataset import CWEClassificationDataset as Dataset

from bugfinder.models.word2vec import Word2VecEmbeddings

from bugfinder.settings import LOGGER
from bugfinder.utils.processing import is_operation_valid

if __name__ == "__main__":
    options = { 
        "word2vec": Word2VecEmbeddings
    }

    parser = argparse.ArgumentParser()

    parser.add_argument("dataset_path", help="Path to the dataset containting the files to generate the embeddings")

    parser.add_argument(
        "--model", "-m", required=True, help="Path to the word2vec model to be used to generated the embeddings",
    )
    parser.add_argument(
        "--emb_length", 
        "-el", 
        required=False,
        default=300,
        type=int, 
        help="Size of the embedding vector to be created",
    )

    args = parser.parse_args()
    kwargs = dict()

    dataset = Dataset(args.dataset_path)

    op_args = {
        "name": 'word2vec',
        "model": args.model,
        "emb_length": args.emb_length,
    }
    
    op_args.update(kwargs)

    operation = {
        "class": options['word2vec'],
        "args": op_args,
    }

    is_operation_valid(operation)

    dataset.queue_operation(operation["class"], operation["args"])

    dataset.process()
