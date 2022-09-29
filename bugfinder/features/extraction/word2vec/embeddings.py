from os import listdir, makedirs
from os.path import join, splitext, exists, dirname, abspath

import numpy as np
import pandas as pd
from abc import abstractmethod
from gensim.models import Word2Vec

from bugfinder.base.processing import AbstractProcessing
from bugfinder.settings import LOGGER


class Word2VecEmbeddings(AbstractProcessing):
    def __init__(self, dataset):
        """Class initialization method."""
        super().__init__(dataset)

        self.embedding_length = 300
        self.vector_length = 50

    def execute(self, **kwargs):
        """Run the processing. Retrieves each tokenized file as a dictionary, loads
        the model, generates the embeddings for each token in the file,
        and saves the embeddings in a CSV file for future processing.
        """
        if "emb_length" in kwargs.keys():
            self.embedding_length = kwargs["emb_length"]

        LOGGER.debug("Retrieving the tokens to transform...")

        token_list = self.get_token_list()

        LOGGER.debug("Token list retrieved. Loading model...")

        embeddings = list()

        model = Word2Vec.load(join(self.dataset.model_dir, kwargs["name"]))

        for item, token in enumerate(token_list):
            LOGGER.debug(
                "Creating the embeddings for %s. %d items left for processing...",
                token["path"],
                (len(token_list) - item),
            )

            try:
                vectors = self.vectorize(model, token)
            except:
                LOGGER.debug("Key not found. Skipping...")
                continue

            tmp = {"path": token["path"], "embeddings": vectors}

            embeddings.append(tmp)

        LOGGER.info("Embeddings created. Saving features...")

        for item in range(len(embeddings)):
            LOGGER.debug(
                "Processing %s file. %d items remaining...",
                embeddings[item]["path"],
                (len(embeddings) - item),
            )
            self.save_dataframe(embeddings[item])

    def save_dataframe(self, embeddings):
        """Saving the generated embeddings in CSV format.

        Args:
            embeddings (pd.DataFrame): Dataframe containing the generated embeddings
        """
        df = pd.DataFrame(embeddings["embeddings"])

        dir_path = dirname(
            abspath(join(self.dataset.embeddings_dir, embeddings["path"]))
        )

        if not exists(dir_path):
            makedirs(dir_path)

        df.to_csv(
            join(self.dataset.embeddings_dir, embeddings["path"]) + ".csv", index=False
        )

    def vectorize(self, model, tokens):
        """Process the token list and generates a matrix containing the token's
        embeddings. The matrix shape is the embedding length X vector_length defined in
        the initialization of the class.
        If the number of tokens of the instance is lower than the embedding length, the
        rest of the matrix is populated with zeros.
        If it's greater, the vector is truncated.

        Args:
            model (gensim.Word2Vec): trained skip-gram model
            nodes (list): list containing all the unique nodes in the dataset

        Returns:
            vectors: a numpy matrix containing the embeddings from the model.
        """
        vectors = np.zeros(shape=(self.embedding_length, self.vector_length))

        for token in range(min(len(tokens["tokens"]), self.embedding_length)):
            vectors[token] = model.wv[tokens["tokens"][token]]

        return vectors

    def get_token_list(self):
        """Reads each file, retrieves the tokens from it and concatenates them in a
        single list which will be the corpus.
        The difference between this function and the one in the Word2VecModel class is
        this one saves the tokens as a
        dictionary where the key is the name of the processed file, so it can be
        identified later for testing/training.

        Returns:
            token_list: list of dictionaries containing all the tokens in the dataset,
            processed from the files
        """
        token_list = list()

        file_processing_list = [
            join(test_case, filepath)
            for test_case in self.dataset.test_cases
            for filepath in listdir(join(self.dataset.path, test_case))
            if splitext(filepath)[1] in [".c", ".h"]
        ]

        while len(file_processing_list) != 0:
            filepath = file_processing_list.pop(0)

            processed_tokens = dict()
            processed_tokens["path"] = splitext(filepath)[0]

            with open(join(self.dataset.path, filepath), "r") as in_file:
                code = in_file.readlines()

                tokens = [token.strip() for token in code]

                LOGGER.debug(
                    "%s file read. Retrieved %d tokens.", filepath, len(tokens)
                )

                processed_tokens["tokens"] = tokens

                token_list.append(processed_tokens)

        return token_list
