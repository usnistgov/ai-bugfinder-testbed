""" 
Bidirectional LSTM classifier.
"""
from os import walk
from os.path import join, basename

import numpy as np
import pandas as pd
from abc import abstractmethod
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split

from tensorflow.keras.layers import Dense, Dropout, LSTM, Bidirectional, LeakyReLU
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adamax
from tensorflow.keras.utils import to_categorical

from bugfinder.base.processing import AbstractProcessing
from bugfinder.settings import LOGGER


class BLSTMClassifierModel(AbstractProcessing):
    """Class which implements the Bidirectional LSTM model.

    Args:
        AbstractProcessing (_type_): _description_
    """

    def __init__(self, dataset):
        """Class initialization method"""
        super().__init__(dataset)

        self.dropout = 0.5
        self.neurons = 300
        self.num_classes = 2
        self.learning_rate = 0.002

        self.embedding_length = 300
        self.vector_length = 50

        self.results = None

    @abstractmethod
    def init_model(self, name, **kwargs):
        """Setup the model. Abstract method."""
        raise NotImplementedError()

    @staticmethod
    def _retrieve_file_list(input_path):
        """Reads every file in the input path given as input and returns a list with
        the path of all CSV files in the tree directory. Should be used in this context on
        the created embeddings directory

        Args:
            input_path (str): string with the path of the dataset

        Returns:
            filelist(str): list of strings with all CSV files
        """
        file_list = []

        for dirs, subdirs, files in walk(input_path):
            for file in files:
                if basename(file).endswith(".csv"):
                    file_list.append(join(dirs, file))

        return file_list

    def _load_dataset(self):
        """Reads the file list and processes them to generate the dataset which will be used in the LSTM training phase.
        The embeddings and the labels are saved in a numpy array, which will be reshaped after finishing the read from disk.

        Returns:
            vectors(np.array): vectors containing the embeddings from the processed instances
            labels(np.array): vector containing the labels for each instance
        """
        LOGGER.debug("Loading the dataset which will be used for training...")

        labels = list()
        vectors = list()

        file_processing_list = self._retrieve_file_list(self.dataset.embeddings_dir)

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

    def _build_model(self, embedding_length, vector_length):
        """Build the model using the Sequential() object

        Args:
            embedding_length (int): Embedding length which is used for the input layer
            vector_length (int): Vector length  which is used for the input layer

        Returns:
            model(Sequential): Keras model
        """
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

    @staticmethod
    def evaluate(model, weights_path, batch_size, x_test, y_test):
        """Evaluates the model using several metrics.

        Args:
            model (Sequential): the model representation
            weights_path (str): path for the model's weight file to be loaded
            batch_size (int): batch size of the testing set
            x_test (np.array): testing instances
            y_test (np.array): testing labels
        """
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

    def execute(self, name, **kwargs):
        """Run the model training and evaluation.

        Args:
            name (str): This parameter will be the name of the model saved in disk.
        """
        # self.embedding_length = kwargs["emb_length"]

        self.embedding_length = kwargs.get("emb_length", 300)
        self.vector_length = kwargs.get("vec_length", 50)
        self.epochs = kwargs.get("epochs", 10)
        self.batch_size = kwargs.get("batch_size", 64)

        vectors, labels = self._load_dataset()

        x_train, x_test, y_train, y_test = train_test_split(
            vectors, labels, test_size=0.2, random_state=101
        )

        y_train = to_categorical(y_train)
        y_test = to_categorical(y_test)

        LOGGER.info("Building the Bidirectional LSTM...")

        model = self._build_model(self.embedding_length, self.vector_length)

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


class BLSTMClassifierTraining(BLSTMClassifierModel):
    """Bidirectional Long Short-Term Memory classifier"""

    def __init__(self, dataset):
        """Class initialization method"""
        super().__init__(dataset)

    def init_model(self, **kwargs):
        """Setup the model"""
        LOGGER.debug("Bidirectional LSTM class")
