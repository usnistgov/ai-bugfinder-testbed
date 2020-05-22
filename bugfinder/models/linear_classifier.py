""" Linear classifier for the dataset.
"""
import tensorflow as tf

from bugfinder.models import ClassifierModel


class LinearClassifierTraining(ClassifierModel):
    def __init__(self, dataset):
        super().__init__(dataset)
        self.model_cls = tf.estimator.LinearClassifier

    def init_model(self, model_dir, **kwargs):
        return self.model_cls(
            feature_columns=[
                tf.feature_column.numeric_column(col) for col in self.columns
            ],
            n_classes=2,
            model_dir=model_dir,
        )
