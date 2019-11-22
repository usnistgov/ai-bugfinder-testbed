""" Linear classifier for the dataset
"""
from os.path import join

import tensorflow as tf
from tools.models import ClassifierModel
from tools.settings import LOGGER


class LinearClassifierTraining(ClassifierModel):
    def __init__(self, dataset):
        super().__init__(dataset)
        self.model_cls = tf.estimator.LinearClassifier
        self.model_dir = join(
            self.dataset.feats_dir, "models", "dnn_classifier"
        )

    def train(self):
        model = self.model_cls(
            feature_columns=[
                tf.feature_column.numeric_column(col)
                for col in self.columns
            ],
            n_classes=2,
            model_dir=self.model_dir
        )

        model.train(input_fn=self.train_fn, steps=100)
        results = model.evaluate(self.test_fn)

        LOGGER.debug("Training accuracy: %f" % results["accuracy"])
