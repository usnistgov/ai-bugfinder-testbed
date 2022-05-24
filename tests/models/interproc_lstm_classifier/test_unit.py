from unittest import TestCase
from unittest.mock import Mock

from bugfinder.dataset import CWEClassificationDataset
from bugfinder.models.interproc_lstm_classifier import InterprocLSTMTraining
import tensorflow as tf


class TestInterprocLSTMTrainingInit(TestCase):
    def setUp(self) -> None:
        dataset = Mock(spec=CWEClassificationDataset)
        self.dataset_processing = InterprocLSTMTraining(dataset)

    def test_model_cls_initialized(self):
        self.assertEqual(self.dataset_processing.model_cls, tf.keras.models.Sequential)
