""" Abstract classifier model for the dataset.
"""
from os import listdir, makedirs, walk
from os.path import join, split, exists, splitext, dirname, abspath, basename

import numpy as np
import pandas as pd
import tensorflow as tf
import networkx as nx

from abc import abstractmethod
from gensim.models import Word2Vec
from shutil import rmtree, copytree
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from tensorflow.keras.layers import Dense, Dropout, LSTM, Bidirectional, LeakyReLU
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adamax
from tensorflow.keras.utils import to_categorical

from bugfinder.dataset.processing import DatasetProcessing, DatasetProcessingCategory
from bugfinder.settings import LOGGER
from bugfinder.utils.statistics import has_better_metrics
from bugfinder.features.extraction.node2vec.impl import Node2VecImplementation


class Node2VecModel(DatasetProcessing):
    def __init__(self, dataset):
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
        raise NotImplementedError()

    #########################

    def execute(self, name, **kwargs):
        self.vector_length = kwargs["vec_length"]

        LOGGER.info("Creating the graph representation for training...")

        edges = self.get_all_edges()

        graph = nx.Graph()
        graph = nx.from_pandas_edgelist(edges, "start", "end")

        LOGGER.debug("Number of nodes in the graph: %d nodes", len(graph.nodes()))
        LOGGER.debug("Number of edges in the graph: %d edges", len(graph.edges))

        LOGGER.info("Initializing node2vec model...")

        node2vec = Node2VecImplementation(
            graph,
            dimensions=self.vector_length,
            walk_length=self.walk_length,
            num_walks=self.num_walks,
            p=self.p,
            q=self.q,
            seed=self.seed,
        )

        model = node2vec.fit(
            window=self.window_dim,
            min_count=self.min_count,
            vector_size=self.vector_length,
            workers=self.workers,
            sg=self.algorithm,
            seed=self.seed,
        )

        LOGGER.info("Training complete. Saving the model...")

        model_dir = join(self.dataset.model_dir, name)

        if not exists(self.dataset.model_dir):
            makedirs(self.dataset.model_dir)

        model.save(model_dir)

    #########################

    def get_all_edges(self):
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


#########################################


class Node2VecEmbeddingsBase(DatasetProcessing):
    def __init__(self, dataset):
        super().__init__(dataset)

        self.embedding_length = 50
        self.vector_length = 64

    @abstractmethod
    def init_model(self, name, **kwargs):
        raise NotImplementedError()

    #########################

    def execute(self, name, **kwargs):
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

    #########################

    def _get_nodes_list(self):
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

                    # TODO: find a way to create the unique node list without creating the graph
                    graph = nx.Graph()
                    graph = nx.from_pandas_edgelist(csv_edge_file, "start", "end")

                    file_nodes = list(graph.nodes())

                    processed_nodes["nodes"] = file_nodes

                    nodes_list.append(processed_nodes)

        return nodes_list

    #########################

    def _save_dataframe(self, embeddings):
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
        vectors = np.zeros(shape=(self.embedding_length, self.vector_length))

        for node in range(min(len(nodes["nodes"]), self.embedding_length)):
            vectors[node] = model.wv[str(nodes["nodes"][node])]

        return vectors


#########################################
class Word2VecModel(DatasetProcessing):
    def __init__(self, dataset):
        super().__init__(dataset)

        self.tokens = {}

        self.word_dim = 50
        self.window_dim = 5
        self.min_count = 1
        self.workers = 4
        self.algorithm = 1  # 1 = skipgram
        self.seed = 32

    @abstractmethod
    def init_model(self, name, **kwargs):
        raise NotImplementedError()

    def execute(self, name, **kwargs):
        LOGGER.debug("Generating the token list for training...")

        token_list = self.get_token_list()

        LOGGER.debug("Training the word2vec model.")

        model = Word2Vec(
            token_list,
            min_count=self.min_count,
            vector_size=self.word_dim,
            workers=self.workers,
            sg=self.algorithm,
            seed=self.seed,
        )

        LOGGER.debug("Training complete. Saving the model...")

        model_dir = join(self.dataset.model_dir, name)

        if not exists(self.dataset.model_dir):
            makedirs(self.dataset.model_dir)

        model.save(model_dir)

    #########################

    def get_token_list(self):
        token_list = list()

        file_processing_list = [
            join(test_case, filepath)
            for test_case in self.dataset.test_cases
            for filepath in listdir(join(self.dataset.path, test_case))
            if splitext(filepath)[1] in [".c", ".h"]
        ]

        while len(file_processing_list) != 0:
            filepath = file_processing_list.pop(0)
            # LOGGER.debug(filepath.split('/')[0])

            with open(join(self.dataset.path, filepath), "r") as in_file:
                code = in_file.readlines()

                tokens = [token.strip() for token in code]
                token_list.append(tokens)

        return token_list


#########################################
class Word2VecEmbeddingsBase(DatasetProcessing):
    def __init__(self, dataset):
        super().__init__(dataset)

        self.embedding_length = 300
        self.vector_length = 50

    @abstractmethod
    def init_model(self, name, **kwargs):
        raise NotImplementedError()

    def execute(self, name, **kwargs):
        if "emb_length" in kwargs.keys():
            self.embedding_length = kwargs["emb_length"]

        LOGGER.debug("Retrieving the tokens to transform...")

        token_list = self.get_token_list()

        LOGGER.debug("Token list retrieved. Loading model...")

        embeddings = list()

        model = Word2Vec.load(join(self.dataset.model_dir, kwargs["model"]))

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

    #########################

    def save_dataframe(self, embeddings):
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

    def vectorize(self, model, tokens):
        vectors = np.zeros(shape=(self.embedding_length, self.vector_length))

        for token in range(min(len(tokens["tokens"]), self.embedding_length)):
            vectors[token] = model.wv[tokens["tokens"][token]]

        return vectors

    #########################

    def get_token_list(self):
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


#########################################
class BLSTMClassifierModel(DatasetProcessing):
    def __init__(self, dataset):
        super().__init__(dataset)

        self.dropout = 0.5
        self.neurons = 300
        self.num_classes = 2
        self.learning_rate = 0.002

        self.embedding_length = 300
        self.vector_length = 50

        self.results = None

    #########################

    @abstractmethod
    def init_model(self, name, **kwargs):
        raise NotImplementedError()

    #########################

    @staticmethod
    def retrieve_file_list(input_path):
        file_list = []

        for dirs, subdirs, files in walk(input_path):
            for file in files:
                if basename(file).endswith(".csv"):
                    file_list.append(join(dirs, file))

        return file_list

    #########################

    def load_dataset(self):
        LOGGER.debug("Loading the dataset which will be used for training...")

        labels = list()
        vectors = list()

        file_processing_list = self.retrieve_file_list(self.dataset.embeddings_dir)

        while len(file_processing_list) != 0:
            filepath = file_processing_list.pop(0)

            # TODO: Workaround to get the class.
            if "good" in filepath:
                labels.append(0)
            else:
                labels.append(1)

            LOGGER.debug(
                "Reading embeddings from %s (%d items left)...",
                filepath,
                len(file_processing_list),
            )

            df = pd.read_csv(filepath)

            vectors.append(df.to_numpy())

            del df

        LOGGER.debug("Reshaping vectors...")

        vectors = np.dstack(vectors)
        vectors = vectors.reshape(-1, self.embedding_length, self.vector_length)

        labels = np.array(labels)
        labels = labels.reshape(labels.shape + (1,))

        return vectors, labels

    #########################

    def build_model(self, embedding_length, vector_length):
        model = Sequential()

        model.add(
            Bidirectional(
                LSTM(self.neurons), input_shape=(embedding_length, vector_length)
            )
        )
        model.add(Dense(self.neurons))
        model.add(LeakyReLU())
        model.add(Dropout(self.dropout))
        model.add(Dense(self.neurons))
        model.add(LeakyReLU())
        model.add(Dropout(self.dropout))
        model.add(Dense(2, activation="softmax"))

        adamax = Adamax(learning_rate=self.learning_rate)

        model.compile(adamax, "categorical_crossentropy", metrics=["accuracy"])

        return model

    #########################

    @staticmethod
    def evaluate(model, weights_path, batch_size, x_test, y_test):
        model.load_weights(weights_path)

        values = model.evaluate(x_test, y_test, batch_size=batch_size)

        LOGGER.info("Accuracy: %02.03f%%", (values[1] * 100))

        predictions = (model.predict(x_test, batch_size=batch_size)).round()

        tn, fp, fn, tp = confusion_matrix(
            np.argmax(y_test, axis=1), np.argmax(predictions, axis=1)
        ).ravel()

        LOGGER.info("False positive rate : %02.03f%%", (fp / (fp + tn) * 100))
        LOGGER.info("False negative rate is: %02.03f%%", (fn / (fn + tp) * 100))

        recall = tp / (tp + fn)
        precision = tp / (tp + fp)
        fscore = (2 * precision * recall) / (precision + recall)

        LOGGER.info(
            "Precision: %02.03f%%; Recall: %02.03f%%; F-score: %02.03f%% ",
            precision * 100,
            recall * 100,
            fscore * 100,
        )

    #########################

    def execute(self, name, **kwargs):
        # self.embedding_length = kwargs["emb_length"]

        self.embedding_length = kwargs.get("emb_length", 300)
        self.vector_length = kwargs.get("vec_length", 50)
        self.epochs = kwargs.get("epochs", 10)
        self.batch_size = kwargs.get("batch_size", 64)

        vectors, labels = self.load_dataset()

        x_train, x_test, y_train, y_test = train_test_split(
            vectors, labels, test_size=0.2, random_state=101
        )

        y_train = to_categorical(y_train)
        y_test = to_categorical(y_test)

        LOGGER.info("Building the Bidirectional LSTM...")

        model = self.build_model(self.embedding_length, self.vector_length)

        LOGGER.info(
            "Training the Bidirectional LSTM on %d items over %d epochs. "
            "Testing on %d items...",
            len(x_train),
            self.epochs,
            len(x_test),
        )

        model.fit(x_train, y_train, batch_size=self.batch_size, epochs=self.epochs)

        LOGGER.info("Training complete. Saving the model weights...")

        model_dir = join(self.dataset.model_dir, name)

        model.save_weights(model_dir)

        LOGGER.info("Evaluating...")

        self.evaluate(model, model_dir, self.batch_size, x_test, y_test)


#########################################
class ClassifierModel(DatasetProcessing):
    """Abstract class for classifier models"""

    def __init__(self, dataset):
        """Class instantiation method"""
        super().__init__(dataset)

        self.metadata["category"] = str(DatasetProcessingCategory.TRAINING)
        self.model_cls = None
        self.train_fn = None
        self.test_fn = None
        self.columns = None

    @abstractmethod
    def init_model(self, name, **kwargs):
        """Setup the model. Abstract method."""
        raise NotImplementedError()

    def execute(
        self,
        name,
        batch_size=100,
        max_items=None,
        epochs=1,
        result_focus=None,
        keep_best_model=False,
        reset=False,
        **kwargs,
    ):
        """Train the model."""
        last_results = None

        if self.model_cls is None:
            raise Exception("Parameter 'model_cls' is undefined")

        if result_focus is None:
            result_focus = ["f1-score"]

        output_data = self.dataset.features["result"]
        input_data = self.dataset.features.drop(["result", "name"], axis=1)

        # Renaming input columns to avoid forbidden characters
        input_data.columns = [
            "feat%03d" % feature_nb for feature_nb in range(len(input_data.columns))
        ]

        input_train, input_test, output_train, output_test = train_test_split(
            input_data, output_data, test_size=0.33, random_state=101
        )

        LOGGER.info(
            "Training %s on %d items over %d epochs. Testing on %d items, "
            "focusing on %s...",
            self.model_cls.__name__,
            (
                len(input_train)
                if max_items is None
                else min(max_items, len(input_train))
            ),
            epochs,
            len(input_test),
            ",".join(result_focus),
        )

        self.columns = input_train.columns

        self.train_fn = tf.compat.v1.estimator.inputs.pandas_input_fn(
            x=input_train,
            y=output_train,
            shuffle=True,
            batch_size=batch_size,
        )
        self.test_fn = tf.compat.v1.estimator.inputs.pandas_input_fn(
            x=input_test, y=output_test, shuffle=False, batch_size=batch_size
        )

        # Initialize model dir and backup dir
        model_dir = join(self.dataset.model_dir, name)
        if reset and exists(model_dir):
            LOGGER.info("Removing %s...", model_dir)
            rmtree(model_dir)

        model_dir_bkp = "%s.bkp" % model_dir

        # Initialize statistics
        self.processing_stats = {
            "samples": {"training": len(input_train), "testing": len(input_test)},
            "results": None,
        }

        if name in self.dataset.summary["training"] and not reset:
            last_results = self.dataset.summary["training"][name]["last_results"]

        # Check if results need to be recalculated
        need_evaluate_model = False
        if last_results is None and not reset and exists(model_dir):
            LOGGER.warning(
                "Summary tampered with, creating baseline on current testing data..."
            )
            need_evaluate_model = True

        model = self.init_model(model_dir, **kwargs)

        if need_evaluate_model:  # Evaluate the model if needed
            preds_test = [
                int(pred["classes"][0]) for pred in model.predict(input_fn=self.test_fn)
            ]

            last_results = classification_report(
                output_test,
                preds_test,
                target_names=self.dataset.classes,
                output_dict=True,
            )["weighted avg"]

            LOGGER.info("Report generated for existing model.")

        # Backup the existing model if needs be
        if exists(model_dir_bkp):
            rmtree(model_dir_bkp)

        if last_results is not None and keep_best_model:
            copytree(model.model_dir, model_dir_bkp)

        # Train the model for the given number of epochs
        for epoch_num in range(epochs):
            LOGGER.info("Training dataset for epoch %d/%d...", epoch_num + 1, epochs)
            model.train(input_fn=self.train_fn, steps=max_items)

        # Evaluate the model and save the predictions
        preds_test = [
            int(pred["classes"][0]) for pred in model.predict(input_fn=self.test_fn)
        ]

        self.processing_stats["results"] = classification_report(
            output_test,
            preds_test,
            target_names=self.dataset.classes,
            output_dict=True,
        )

        current = {
            "precision": self.processing_stats["results"]["weighted avg"]["precision"]
            * 100,
            "recall": self.processing_stats["results"]["weighted avg"]["recall"] * 100,
            "f1-score": self.processing_stats["results"]["weighted avg"]["f1-score"]
            * 100,
        }

        last = {
            "precision": float("nan"),
            "recall": float("nan"),
            "f1-score": float("nan"),
        }

        if last_results is not None:
            last = {
                "precision": last_results["precision"] * 100,
                "recall": last_results["recall"] * 100,
                "f1-score": last_results["f1-score"] * 100,
            }

        LOGGER.info(
            "Precision: %02.03f%% (%02.03f%%); Recall: %02.03f%% (%02.03f%%); "
            "F-score: %02.03f%% (%02.03f%%).",
            current["precision"],
            last["precision"],
            current["recall"],
            last["recall"],
            current["f1-score"],
            last["f1-score"],
        )

        if keep_best_model and not has_better_metrics(
            result_focus,
            self.processing_stats["results"]["weighted avg"],
            last_results,
        ):
            LOGGER.warning(
                "Performance decreased from original values. Replacing model with "
                "previous one..."
            )
            rmtree(model_dir)
            copytree(model_dir_bkp, model_dir)
        else:
            self.processing_stats["last_results"] = self.processing_stats["results"][
                "weighted avg"
            ]

        if exists(model_dir_bkp):
            rmtree(model_dir_bkp)
