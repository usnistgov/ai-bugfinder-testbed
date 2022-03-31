from unittest import TestCase
from unittest.mock import Mock

from bugfinder.dataset import CodeWeaknessClassificationDataset
from bugfinder.models.dnn_classifier import DNNClassifierTraining
import tensorflow as tf


class TestDNNClassifierTrainingInit(TestCase):
    def setUp(self) -> None:
        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        self.dataset_processing = DNNClassifierTraining(dataset)

    def test_model_cls_initialized(self):
        self.assertEqual(self.dataset_processing.model_cls, tf.estimator.DNNClassifier)


class TestDNNClassifierTrainingInitModel(TestCase):
    def setUp(self) -> None:
        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        self.dataset_processing = DNNClassifierTraining(dataset)
        self.dataset_processing.columns = ["feature1", "feature2"]

    def test_default_architecture_set(self):
        model = self.dataset_processing.init_model("mock_dir")
        # FIXME: Cannot test architecture so testing the output only
        self.assertEqual(type(model), tf.estimator.DNNClassifier)

    def test_can_set_architecture(self):
        model = self.dataset_processing.init_model("mock_dir", architecture=[5, 5])
        # FIXME: Cannot test architecture so testing the output only
        self.assertEqual(type(model), tf.estimator.DNNClassifier)
