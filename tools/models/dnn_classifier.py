"""
"""
from os.path import join

import tensorflow as tf
from tools.models import ClassifierModel
from tools.settings import LOGGER


class DNNClassifierTraining(ClassifierModel):
    def __init__(self, dataset):
        super().__init__(dataset)
        self.model_cls = tf.estimator.DNNClassifier
        self.model_dir = join(
            self.dataset.feats_dir, "models", "dnn_classifier"
        )

    def train(self):
        model = self.model_cls(
            hidden_units=[10, 10, 10],
            feature_columns=[
                tf.feature_column.numeric_column(col)
                for col in self.columns
            ],
            n_classes=2,
            model_dir=self.model_dir
        )

        model.train(input_fn=self.train_fn, steps=100)
        results = model.evaluate(self.test_fn)

        pr = results["precision"]
        rc = results["recall"]
        fs = 2 * pr * rc / (pr + rc)

        LOGGER.debug("Precision: %d%%; Recall: %d%%; F-score: %d%%" %
                     (pr, rc, fs))
