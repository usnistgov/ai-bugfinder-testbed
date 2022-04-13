from collections import defaultdict

import networkx as nx
import numpy as np
import random
from gensim.models import Word2Vec

from bugfinder.settings import LOGGER

"""
node2vec implementation based on eliorc's module on PyPi
"""


class Node2VecImplementation:
    """An implementation of the node2vec algorithm based on eliorc's module on PyPi."""

    FIRST_TRAVEL_KEY = "first_travel_key"
    PROBABILITIES_KEY = "probabilities"
    NEIGHBORS_KEY = "neighbors"
    WEIGHT_KEY = "weight"
    NUM_WALKS_KEY = "num_walks"
    WALK_LENGTH_KEY = "walk_length"
    P_KEY = "p"
    Q_KEY = "q"

    def __init__(
        self,
        graph,
        dimensions=64,
        walk_length=80,
        num_walks=10,
        p=1,
        q=1,
        weight_key="weight",
        workers=1,
        sampling_strategy=None,
        seed=None,
    ):
        """Initialize the algorithm and generates the random walks which will be used by the skip-gram algorithm to generate the embeddings.

        Args:
            graph (nx.Graph): networkx graph type. Node names must be strings or ints.
            dimensions (int, optional): Number of dimensions the embedding will have. Defaults to 64.
            walk_length (int, optional): Number of nodes visited in each walk. Defaults to 80.
            num_walks (int, optional): Number of walks per node. Defaults to 10.
            p (int, optional): Return hyperparameter. Defaults to 1.
            q (int, optional): Inout parameter. Defaults to 1.
            weight_key (str, optional): Used in weighted graphs. Defaults to "weight".
            workers (int, optional): Number of workers used by the word2vec algorithm when training the corpus. Defaults to 1.
            sampling_strategy (_type_, optional): Node specific sampling strategies. Not used in this implementation since it's the same as using the global hyperparameters. Defaults to None.
            seed (_type_, optional): Seed for deterministic results. Needs to be used with workers=1. Defaults to None.
        """

        self.graph = graph
        self.dimensions = dimensions
        self.walk_length = walk_length
        self.num_walks = num_walks
        self.p = p
        self.q = q
        self.weight_key = weight_key
        self.workers = workers
        self.d_graph = defaultdict(dict)

        if sampling_strategy is None:
            self.sampling_strategy = {}
        else:
            self.sampling_strategy = sampling_strategy

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self._precompute_probabilities()
        self.walks = self._generate_walks(
            self.d_graph,
            self.walk_length,
            self.num_walks,
            self.sampling_strategy,
            self.NUM_WALKS_KEY,
            self.WALK_LENGTH_KEY,
            self.NEIGHBORS_KEY,
            self.PROBABILITIES_KEY,
            self.FIRST_TRAVEL_KEY,
        )

    #########################

    def _precompute_probabilities(self):
        """Pre-compute the transition probabilities used for guiding the random walks."""
        LOGGER.debug("Precomputing probabilities for the random walks...")

        d_graph = self.d_graph

        nodes_generator = self.graph.nodes()

        for source in nodes_generator:
            if self.PROBABILITIES_KEY not in d_graph[source]:
                d_graph[source][self.PROBABILITIES_KEY] = dict()

            for current_node in self.graph.neighbors(source):
                if self.PROBABILITIES_KEY not in d_graph[current_node]:
                    d_graph[current_node][self.PROBABILITIES_KEY] = dict()

                unnormalized_weights = list()
                d_neighbors = list()

                for destination in self.graph.neighbors(current_node):

                    p = (
                        self.sampling_strategy[current_node].get(self.P_KEY, self.p)
                        if current_node in self.sampling_strategy
                        else self.p
                    )
                    q = (
                        self.sampling_strategy[current_node].get(self.Q_KEY, self.q)
                        if current_node in self.sampling_strategy
                        else self.q
                    )

                    if destination == source:
                        ss_weight = (
                            self.graph[current_node][destination].get(
                                self.weight_key, 1
                            )
                            * 1
                            / p
                        )
                    elif destination in self.graph[source]:
                        ss_weight = self.graph[current_node][destination].get(
                            self.weight_key, 1
                        )
                    else:
                        ss_weight = (
                            self.graph[current_node][destination].get(
                                self.weight_key, 1
                            )
                            * 1
                            / q
                        )

                    unnormalized_weights.append(ss_weight)
                    d_neighbors.append(destination)

                unnormalized_weights = np.array(unnormalized_weights)
                d_graph[current_node][self.PROBABILITIES_KEY][source] = (
                    unnormalized_weights / unnormalized_weights.sum()
                )

            first_travel_weights = []

            for destination in self.graph.neighbors(source):
                first_travel_weights.append(
                    self.graph[source][destination].get(self.weight_key, 1)
                )

            first_travel_weights = np.array(first_travel_weights)
            d_graph[source][self.FIRST_TRAVEL_KEY] = (
                first_travel_weights / first_travel_weights.sum()
            )

            d_graph[source][self.NEIGHBORS_KEY] = list(self.graph.neighbors(source))

        LOGGER.debug("Finished.")

    #########################

    def _generate_walks(
        self,
        d_graph: dict,
        global_walk_length: int,
        num_walks: int,
        sampling_strategy: dict = None,
        num_walks_key: str = None,
        walk_length_key: str = None,
        neighbors_key: str = None,
        probabilities_key: str = None,
        first_travel_key: str = None,
    ) -> list:
        """Generates the random walks which will be used by the skip-gram algorithm to generate the embeddings

        Args:
            d_graph (dict): graph containing the nodes and edges used as input for the the algorithm
            global_walk_length (int): Number of nodes visited in each walk.
            num_walks (int): Number of walks per node.
            sampling_strategy (dict, optional): Node specific sampling strategies. Defaults to None.
            num_walks_key (str, optional): Defaults to None.
            walk_length_key (str, optional): Defaults to None.
            neighbors_key (str, optional): Defaults to None.
            probabilities_key (str, optional): Defaults to None.
            first_travel_key (str, optional): Defaults to None.

        Returns:
            list: List containing the random walks generated by the algorithm
        """

        walks = list()

        for n_walk in range(num_walks):
            shuffled_nodes = list(d_graph.keys())
            random.shuffle(shuffled_nodes)

            for source in shuffled_nodes:
                if (
                    source in sampling_strategy
                    and num_walks_key in sampling_strategy[source]
                    and sampling_strategy[source][num_walks_key] <= n_walk
                ):
                    continue

                walk = [source]

                if source in sampling_strategy:
                    walk_length = sampling_strategy[source].get(
                        walk_length_key, global_walk_length
                    )
                else:
                    walk_length = global_walk_length

                while len(walk) < walk_length:
                    walk_options = d_graph[walk[-1]].get(neighbors_key, None)

                    if not walk_options:
                        break

                    if len(walk) == 1:  # For the first step
                        probabilities = d_graph[walk[-1]][first_travel_key]
                        walk_to = random.choices(walk_options, weights=probabilities)[0]
                    else:
                        probabilities = d_graph[walk[-1]][probabilities_key][walk[-2]]
                        walk_to = random.choices(walk_options, weights=probabilities)[0]

                    walk.append(walk_to)

                walk = list(map(str, walk))

                walks.append(walk)

        LOGGER.debug("Random walk finished. Returning list...")

        return walks

    #########################

    def fit(self, **skip_gram_params) -> Word2Vec:
        """Creates the embeddings using the skip-gram algorithm. Accepts any input the Word2Vec model accepts in a dict format, so it`s possible to tune the algorithm if necessary.

        Returns:
            Word2Vec: Trained model.
        """
        if "vector_size" not in skip_gram_params:
            skip_gram_params["vector_size"] = self.dimensions

        if "sg" not in skip_gram_params:
            skip_gram_params["sg"] = 1

        LOGGER.debug("Training model...")

        model = Word2Vec(self.walks, **skip_gram_params)

        LOGGER.debug("Finished.")

        return model
