from glob import glob
from os import makedirs, listdir
from os.path import join, exists, splitext, split, dirname, abspath

import networkx as nx
import numpy as np
import pandas as pd
from gensim.models import Word2Vec

from bugfinder import settings
from bugfinder.base.processing import AbstractProcessing
from bugfinder.settings import LOGGER


class Node2VecEmbeddings(AbstractProcessing):
    """Class responsible for generating the embeddings, using the Word2Vec model
    trained with the output of the node2vec algorithm.
    """

    embedding_length = 50
    vector_length = 64

    def execute(self, **kwargs):
        """Run the processing. This function reads again the dataset looking for the
        edges files generated by Joern, process them and generates a embedding vector
        for each instance.

        Returns:
            embeddings(dict): dictionary containing all embeddings
        """
        self.embedding_length = kwargs["emb_length"]
        self.vector_length = kwargs["vec_length"]

        LOGGER.info("Retrieving the nodes and edges to generate the embeddings...")

        embeddings = list()

        nodes = self._get_nodes_list()

        LOGGER.info("Nodes retrieved. Loading the model...")

        model = Word2Vec.load(join(self.dataset.model_dir, kwargs["name"]))

        for item, node in enumerate(nodes):
            LOGGER.debug(
                "Creating the embeddings for %s. %d items left for processing...",
                node["path"],
                (len(nodes) - item),
            )

            # TODO: Change this exception to the vectorize function
            try:
                vectors = self._vectorize(model, node)
            except:
                LOGGER.debug("Node not found. Skipping...")
                continue

            tmp = {"path": node["path"], "embeddings": vectors}

            embeddings.append(tmp)

        LOGGER.info("Embeddings created. Saving features...")

        for item in range(len(embeddings)):
            LOGGER.debug(
                "Processing %s file. %d items remaining...",
                embeddings[item]["path"],
                (len(embeddings) - item),
            )

            self._save_dataframe(embeddings[item])

        return embeddings

    #########################

    def _get_nodes_list(self):
        """This function checks for edges CSV files generated by Joern, retrieves the nodes and edges related to
        data and control flows (REACHES and FLOWS_TO) as a dataframe, then reduces it to a list containing only unique nodes.

        Returns:
            nodes_list(list): list containing all the unique nodes in the dataset
        """
        nodes_list = list()

        file_processing_list = glob(
            join(
                self.dataset.path,
                f"{settings.DATASET_DIRS['joern']}/code",
                "*/*/*/*.csv",
            )
        )

        # Reading the edges file to create a graph and retrieve the nodes from it
        # TODO: Refactor this code to a single function to be used across the classes
        while len(file_processing_list) != 0:
            filepath = file_processing_list.pop(0)

            processed_nodes = dict()
            # TODO: Remover the "edge" part from the filepath when saving the string
            processed_nodes["path"] = splitext(filepath)[0]
            processed_nodes["path"] = split(filepath)[0]

            if "edges" in filepath:
                csv_edge_file = pd.read_csv(
                    filepath, sep="\t", usecols=["start", "end", "type"]
                )

                if not csv_edge_file.empty:
                    csv_edge_file = csv_edge_file.loc[
                        (csv_edge_file["type"] == "REACHES")
                        | (csv_edge_file["type"] == "FLOWS_TO")
                    ]

                    # TODO: find a way to create the unique node list without creating
                    #  the graph
                    graph = nx.Graph()
                    graph = nx.from_pandas_edgelist(csv_edge_file, "start", "end")

                    file_nodes = list(graph.nodes())

                    processed_nodes["nodes"] = file_nodes

                    nodes_list.append(processed_nodes)

        return nodes_list

    def _save_dataframe(self, embeddings):
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

    #########################

    def _vectorize(self, model, nodes):
        """Process the node list and generates a matrix containing the node's embeddings.
        The matrix shape is the embedding length X vector_length defined in the initialization of the class.
        If the number of nodes of the instance is lower than the embedding length, the rest of the matrix is populated with zeros.
        If it's greater, the vector is truncated.

        Args:
            model (gensim.Word2Vec): trained skip-gram model
            nodes (list): list containing all the unique nodes in the dataset

        Returns:
            vectors: a numpy matrix containing the embeddings from the model.
        """
        vectors = np.zeros(shape=(self.embedding_length, self.vector_length))

        for node in range(min(len(nodes["nodes"]), self.embedding_length)):
            vectors[node] = model.wv[str(nodes["nodes"][node])]

        return vectors
