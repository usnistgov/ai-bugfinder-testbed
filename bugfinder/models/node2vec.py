from os import makedirs, listdir
from os.path import join, exists, splitext, split, dirname, abspath

import networkx as nx
import numpy as np
import pandas as pd
from abc import abstractmethod
from gensim.models import Word2Vec

from bugfinder.dataset.processing import DatasetProcessing
from bugfinder.features.extraction.node2vec.impl import Node2VecImplementation
from bugfinder.settings import LOGGER


class Node2VecModel(DatasetProcessing):
    """Class for process the dataset and train a word2vec model using the node2vec
    algorithm to generate the corpus used as input
    """

    def __init__(self, dataset):
        """Class initialization method."""
        super().__init__(dataset)

        self.tokens = {}
        self.vector_length = 128
        self.walk_length = 50
        self.num_walks = 10
        self.p = 1
        self.q = 1
        self.window_dim = 10
        self.min_count = 1
        self.workers = 4
        self.algorithm = 1  # 1 = skipgram
        self.seed = 32

    @abstractmethod
    def init_model(self, name, **kwargs):
        """Setup the model. Abstract method."""
        raise NotImplementedError()

    #########################

    def execute(self, name, **kwargs):
        """Run the processing. This function receives the processed dataset, retrieves
        all edges related to data and control flow (REACHES and FLOWS_TO), generates
        the graphs, run the node2vec algorithm to generate the random walks in the
        graphs, creates the model and saves it.

        Args:
            name (str): This parameter will be the name of the model saved in disk.
        """
        self.vector_length = kwargs["vec_length"]

        LOGGER.info("Creating the graph representation for training...")

        # Reads the dataset and saves all edges related to data/control flow
        edges = self._get_all_edges()

        graph = self._create_graph_object(edges)

        LOGGER.debug("Number of nodes in the graph: %d nodes", len(graph.nodes()))
        LOGGER.debug("Number of edges in the graph: %d edges", len(graph.edges))

        LOGGER.info("Initializing node2vec model...")

        # Creates the node2vec object which will execute the algorithm
        node2vec = Node2VecImplementation(
            graph,
            dimensions=self.vector_length,
            walk_length=self.walk_length,
            num_walks=self.num_walks,
            p=self.p,
            q=self.q,
            seed=self.seed,
        )

        # Train the model
        model = node2vec.fit(
            window=self.window_dim,
            min_count=self.min_count,
            vector_size=self.vector_length,
            workers=self.workers,
            sg=self.algorithm,
            seed=self.seed,
        )

        LOGGER.info("Training complete.")

        model_dir = join(self.dataset.model_dir, name)

        if not exists(self.dataset.model_dir):
            makedirs(self.dataset.model_dir)

        LOGGER.info("Saving the model at %s...", model_dir)

        model.save(model_dir)

    #########################

    def _get_all_edges(self):
        """This function checks for edges CSV files generated by Joern, retrieves the
        nodes and edges related to data and control flows (REACHES and FLOWS_TO) as a
        dataframe, and appends each dataframe in a single one.

        Returns:
            edges_dataframe(pd.DataFrame): pandas dataframe containing all the edges
            necessary to create the graph object
        """
        edges_list = list()

        file_processing_list = [
            join(test_case, filepath)
            for test_case in self.dataset.test_cases
            for filepath in listdir(join(self.dataset.path, test_case))
            if splitext(filepath)[1] in [".csv"]
        ]

        while len(file_processing_list) != 0:
            filepath = file_processing_list.pop(0)

            in_path = join(self.dataset.path, filepath)

            if "edges" in in_path:
                csv_edge_file = pd.read_csv(
                    in_path, sep="\t", usecols=["start", "end", "type"]
                )

                if not csv_edge_file.empty:
                    csv_edge_file = csv_edge_file.loc[
                        (csv_edge_file["type"] == "REACHES")
                        | (csv_edge_file["type"] == "FLOWS_TO")
                    ]
                    LOGGER.debug(
                        "Processing %s: %d edges found.",
                        filepath,
                        len(csv_edge_file.index),
                    )

                    edges_list.append(csv_edge_file)
                else:
                    LOGGER.debug("Ignoring %s: Empty dataframe.", filepath)

        LOGGER.info(
            "List of edges succesfully created. %d files read. Creating dataframe...",
            len(edges_list),
        )

        edges_dataframe = pd.concat(edges_list, axis=0, ignore_index=True)

        del edges_list

        return edges_dataframe

    #########################

    def _create_graph_object(self, edges):
        """Creates the graph object used by the node2vec algorithm.

        Args:
            edges_dataframe(pd.DataFrame): pandas dataframe containing all the edges necessary to create the graph object

        Returns:
            graph(nx.Graph): networkx graph type
        """
        graph = nx.Graph()
        graph = nx.from_pandas_edgelist(edges, "start", "end")

        return graph


#########################################


class Node2VecEmbeddingsBase(DatasetProcessing):
    """Class responsible for generating the embeddings, using the Word2Vec model
    trained with the output of the node2vec algorithm.
    """

    def __init__(self, dataset):
        """Class initialization method."""
        super().__init__(dataset)

        self.embedding_length = 50
        self.vector_length = 64

    @abstractmethod
    def init_model(self, name, **kwargs):
        """Setup the model. Abstract method."""
        raise NotImplementedError()

    #########################

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

        model = Word2Vec.load(join(self.dataset.model_dir, kwargs["model"]))

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

        file_processing_list = [
            join(test_case, filepath)
            for test_case in self.dataset.test_cases
            for filepath in listdir(join(self.dataset.path, test_case))
            if splitext(filepath)[1] in [".csv"]
        ]

        # Reading the edges file to create a graph and retrieve the nodes from it
        # TODO: Refactor this code to a single function to be used across the classes
        while len(file_processing_list) != 0:
            filepath = file_processing_list.pop(0)

            processed_nodes = dict()
            # TODO: Remover the "edge" part from the filepath when saving the string
            processed_nodes["path"] = splitext(filepath)[0]
            processed_nodes["path"] = split(filepath)[0]

            in_path = join(self.dataset.path, filepath)

            if "edges" in in_path:
                csv_edge_file = pd.read_csv(
                    in_path, sep="\t", usecols=["start", "end", "type"]
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

    #########################

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


#########################################
class Node2VecTraining(Node2VecModel):
    """Class responsible for the training of the Word2Vec model using the node2vec algorithm output as input for the model."""

    def init_model(self, name, **kwargs):
        """Class initialization method"""
        LOGGER.debug("Class for the Node2Vec training model")


#########################################
class Node2VecEmbeddings(Node2VecEmbeddingsBase):
    """Class responsible for generating the embeddings, using the Word2Vec model trained with the output of the node2vec algorithm."""

    def init_model(self, name, **kwargs):
        """Class initialization method"""
        LOGGER.debug("Class for the Node2Vec embeddings generator")
