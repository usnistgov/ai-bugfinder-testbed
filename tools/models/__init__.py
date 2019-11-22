"""
"""
from abc import abstractmethod
from os.path import join
import pandas as pd
import tensorflow as tf
from tools.dataset.processing import DatasetProcessing
from sklearn.model_selection import train_test_split


class ClassifierModel(DatasetProcessing):
    def __init__(self, dataset):
        super().__init__(dataset)

        self.model_cls = None
        self.train_fn = None
        self.test_fn = None
        self.columns = None

    @abstractmethod
    def train(self):
        raise NotImplementedError()

    def execute(self, network_path=None):
        if self.model_cls is None:
            raise Exception()

        output_data = self.dataset.features["result"]
        input_data = self.dataset.features.drop(["result", "name"], axis=1)

        input_train, input_test, output_train, output_test = train_test_split(
            input_data, output_data, test_size=0.33, random_state=101
        )

        self.columns = input_train.columns

        self.train_fn = tf.estimator.inputs.pandas_input_fn(
            x=input_train, y=output_train, shuffle=True, batch_size=100,
            num_epochs=100
        )
        self.test_fn = tf.estimator.inputs.pandas_input_fn(
            x=input_test, y=output_test, shuffle=False, batch_size=10,
            num_epochs=1
        )

        self.train()
