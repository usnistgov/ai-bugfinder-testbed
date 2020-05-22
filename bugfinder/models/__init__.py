""" Abstract classifier model for the dataset.
"""
from abc import abstractmethod
from os.path import join, exists
from shutil import rmtree

import tensorflow as tf
from sklearn.model_selection import train_test_split

from bugfinder.dataset.processing import DatasetProcessing
from bugfinder.settings import LOGGER


class ClassifierModel(DatasetProcessing):
    def __init__(self, dataset):
        super().__init__(dataset)

        self.model_cls = None
        self.train_fn = None
        self.test_fn = None
        self.columns = None

    @abstractmethod
    def init_model(self, name, **kwargs):
        raise NotImplementedError()

    def execute(self, name, reset=False, **kwargs):
        if self.model_cls is None:
            raise Exception("Parameter 'model_cls' is undefined")

        output_data = self.dataset.features["result"]
        input_data = self.dataset.features.drop(["result", "name"], axis=1)

        # Renaming input columns to avoid forbidden characters
        input_data.columns = [
            "feat%03d" % feature_nb for feature_nb in range(len(input_data.columns))
        ]

        input_train, input_test, output_train, output_test = train_test_split(
            input_data, output_data, test_size=0.33, random_state=101
        )

        self.columns = input_train.columns

        self.train_fn = tf.estimator.inputs.pandas_input_fn(
            x=input_train, y=output_train, shuffle=True, batch_size=100, num_epochs=100
        )
        self.test_fn = tf.estimator.inputs.pandas_input_fn(
            x=input_test, y=output_test, shuffle=False, batch_size=10, num_epochs=1
        )

        # Initialize model
        model_name = join(self.dataset.model_dir, name)
        if reset and exists(model_name):
            LOGGER.info("Removing %s..." % model_name)
            rmtree(model_name)

        model = self.init_model(model_name, **kwargs)

        model.train(input_fn=self.train_fn, steps=100)
        results = model.evaluate(self.test_fn)

        pr = results["precision"]
        rc = results["recall"]
        fs = 2 * pr * rc / (pr + rc)

        LOGGER.info("Precision: %f%%; Recall: %f%%; F-score: %f%%" % (pr, rc, fs))
