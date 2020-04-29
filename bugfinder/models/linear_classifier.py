""" Linear classifier for the dataset
"""
from os.path import join

import tensorflow as tf

from bugfinder.models import ClassifierModel


class LinearClassifierTraining(ClassifierModel):
    def __init__(self, dataset):
        super().__init__(dataset)
        self.model_cls = tf.estimator.LinearClassifier
        self.model_dir = join(self.dataset.feats_dir, "models", "linear_classifier")

    def init_model(self):
        return self.model_cls(
            feature_columns=[
                tf.feature_column.numeric_column(col) for col in self.columns
            ],
            n_classes=2,
            model_dir=self.model_dir,
        )
