""" Deep Neural Net classifier for the dataset.
"""
import tensorflow as tf

from bugfinder.models import ClassifierModel


class DNNClassifierTraining(ClassifierModel):
    def __init__(self, dataset):
        super().__init__(dataset)

        self.model_cls = tf.estimator.DNNClassifier

    def init_model(self, model_dir, **kwargs):
        if "architecture" not in kwargs.keys():
            kwargs["architecture"] = [10, 10, 10]

        return self.model_cls(
            hidden_units=kwargs["architecture"],
            feature_columns=[
                tf.feature_column.numeric_column(col) for col in self.columns
            ],
            n_classes=2,
            model_dir=model_dir,
        )
