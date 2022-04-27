from unittest import TestCase
from unittest.mock import Mock, patch

from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.models.linear_classifier import LinearClassifierTraining

import tensorflow as tf


class TestLinearClassifierTrainingInit(TestCase):
    def setUp(self) -> None:
        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        self.dataset_processing = LinearClassifierTraining(dataset)

    def test_model_cls_assigned(self):
        self.assertEqual(
            self.dataset_processing.model_cls, tf.estimator.LinearClassifier
        )


class TestLinearClassifierTrainingInitModel(TestCase):
    def setUp(self) -> None:
        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        self.dataset_processing = LinearClassifierTraining(dataset)
        self.dataset_processing.columns = ["feat01", "feat02"]

    @patch("tensorflow.estimator.LinearClassifier.__init__")
    def test_model_cls_initialized(self, mock_linear_classfier_init):
        mock_linear_classfier_init.return_value = None
        self.dataset_processing.init_model("mock_dir")
        self.assertTrue(mock_linear_classfier_init.called)
