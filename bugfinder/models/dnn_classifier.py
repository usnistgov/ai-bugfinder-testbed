"""
"""
from os.path import join

import tensorflow as tf

from bugfinder.models import ClassifierModel


class DNNClassifierTraining(ClassifierModel):
    def __init__(self, dataset):
        super().__init__(dataset)
        self.model_cls = tf.estimator.DNNClassifier
        self.model_dir = join(self.dataset.feats_dir, "models", "dnn_classifier")

    def init_model(self):
        return self.model_cls(
            hidden_units=[10, 10, 10],
            feature_columns=[
                tf.feature_column.numeric_column(col) for col in self.columns
            ],
            n_classes=2,
            model_dir=self.model_dir,
        )
