from unittest import TestCase
from unittest.mock import Mock

from bugfinder.dataset import CWEClassificationDataset
from bugfinder.models.linear_classifier import LinearClassifierTraining

import tensorflow as tf


class TestLinearClassifierTrainingInit(TestCase):
    def setUp(self) -> None:
        dataset = Mock(spec=CWEClassificationDataset)
        dataset.feats_dir = "mock_feats_dir"
        self.dataset_processing = LinearClassifierTraining(dataset)

    def test_model_cls_initialized(self):
        self.assertEqual(
            self.dataset_processing.model_cls, tf.estimator.LinearClassifier
        )

    def test_model_dir_initialized(self):
        self.assertEqual(
            self.dataset_processing.model_dir, "mock_feats_dir/models/linear_classifier"
        )
