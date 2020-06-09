""" Abstract classifier model for the dataset.
"""
from abc import abstractmethod
from os.path import join, exists
from shutil import rmtree

import tensorflow as tf
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

from bugfinder.dataset.processing import DatasetProcessing
from bugfinder.settings import LOGGER


class ClassifierModel(DatasetProcessing):
    def __init__(self, dataset):
        super().__init__(dataset)

        self.model_cls = None
        self.training_summary = None
        self.train_fn = None
        self.test_fn = None
        self.columns = None

    @abstractmethod
    def init_model(self, name, **kwargs):
        raise NotImplementedError()

    def execute(self, name, batch_size=100, num_steps=1000, reset=False, **kwargs):
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
            x=input_train, y=output_train, shuffle=True, batch_size=batch_size,
        )
        self.test_fn = tf.estimator.inputs.pandas_input_fn(
            x=input_test, y=output_test, shuffle=False, batch_size=batch_size
        )

        # Initialize model
        model_name = join(self.dataset.model_dir, name)
        if reset and exists(model_name):
            LOGGER.info("Removing %s..." % model_name)
            rmtree(model_name)

        summary = {
            "samples": {"training": len(input_train), "testing": len(input_test)},
            "training": {"time": 0, "steps": num_steps},
            "results": None,
        }
        model = self.init_model(model_name, **kwargs)
        model.train(input_fn=self.train_fn, steps=num_steps)

        preds_test = [
            int(pred["classes"][0]) for pred in model.predict(input_fn=self.test_fn)
        ]

        summary["results"] = classification_report(
            output_test,
            preds_test,
            target_names=self.dataset.classes,
            output_dict=True,
        )

        self.dataset.summary["training"].append(summary)

        pr = summary["results"]["weighted avg"]["precision"] * 100
        rc = summary["results"]["weighted avg"]["recall"] * 100
        fs = summary["results"]["weighted avg"]["f1-score"] * 100

        LOGGER.info(
            "Precision: %02.03f%%; Recall: %02.03f%%; F-score: %02.03f%%" % (pr, rc, fs)
        )
